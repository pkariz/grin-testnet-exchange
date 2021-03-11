from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, transaction
from guardian.shortcuts import assign_perm
from model_utils.models import TimeStampedModel


class Currency(TimeStampedModel):
    
    name = models.CharField(unique=True, max_length=255)
    symbol = models.SlugField(unique=True, max_length=255)

    class Meta:
        verbose_name_plural = "currencies"

    def __str__(self):
        return self.name


class Balance(TimeStampedModel):

    currency = models.ForeignKey(
        Currency,
        related_name='balances',
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        User,
        related_name='balances',
        on_delete=models.CASCADE,
    )
    amount = models.DecimalField(
        max_digits=30,
        decimal_places=9,
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(2**64)]
    )
    locked_amount = models.DecimalField(
        max_digits=30,
        decimal_places=9,
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(2**64)]
    )

    def __str__(self):
        return '{}, total: {}, locked: {}, user: {}'.format(
            self.currency.symbol,
            self.amount,
            self.locked_amount,
            self.user.username
        )
    @transaction.atomic
    def save(self, *args, **kwargs):
        """Needed to manually run validators on amounts."""
        # full_clean runs validators
        self.full_clean()
        return super().save(*args, **kwargs)


class Deposit(TimeStampedModel):

    STATUSES = (
        ('awaiting transaction signature', 'awaiting transaction signature'),
        ('awaiting confirmation', 'awaiting confirmation'),
        ('finished', 'finished'),
        ('canceled', 'canceled'),
    )
    balance = models.ForeignKey(
        Balance,
        related_name='deposits',
        on_delete=models.CASCADE,
    )
    amount = models.DecimalField(
        max_digits=30,
        decimal_places=9,
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(2**64)]
    )
    status = models.CharField(max_length=255, choices=STATUSES)
    confirmations = models.IntegerField(
        validators=[MinValueValidator(0)],
        default=0
    )
    # tx_slate_id is needed in case when we want to cancel the deposit after the
    # first step of RSR (eg. when new deposit is initiated)
    tx_slate_id = models.CharField(unique=True, max_length=255)
    # we store kernel excess to update number of confirmations
    kernel_excess = models.CharField(
        unique=True, null=True, blank=True, max_length=255)

    class Meta:
        ordering = ['created']

    def __str__(self):
        return '{}, amount: {}, status: {}, user:{}'.format(
            self.balance.currency.symbol,
            self.amount,
            self.status,
            self.balance.user.username
        )

    @transaction.atomic
    def save(self, *args, **kwargs):
        """On deposit create set permissions"""
        created = self.pk is None
        if not created:
            current_deposit = Deposit.objects.get(pk=self.pk)
            if (
                current_deposit.status == 'awaiting transaction signature' and
                self.status == 'awaiting confirmation'
            ):
                # finished the transaction, lock amount in balance
                balance = self.balance
                balance.locked_amount = balance.locked_amount + self.amount
                balance.save()
            elif (
                self.status == 'awaiting confirmation' and
                self.confirmations == settings.REQUIRED_CONFIRMATIONS
            ):
                self.status = 'finished'
                # deposit completed, transfer locked amount to available amount
                balance = self.balance
                balance.locked_amount = balance.locked_amount - self.amount
                balance.amount = balance.amount + self.amount
                balance.save()

        # full_clean runs validators
        self.full_clean()
        res = super().save(*args, **kwargs)
        if created:
            assign_perm('api.view_deposit', self.balance.user, self)

        return res

    @transaction.atomic
    def delete(self, **kwargs):
        # we need to remove locked amount from balance if anything is locked
        # NOTE: this can also be called on an already confirmed deposit in
        # which case nothing is locked
        if self.status == 'awaiting confirmation':
            # it means it's still waiting signature or confirmations in which
            # case deposit's amount is locked in its balance
            balance = self.balance
            balance.locked_amount = balance.locked_amount - self.amount
            balance.save()
            # NOTE: we should cancel tx here, but it's more explicit to do it
            # in the view. The downside is that when we delete it through a
            # shell we need to manually cancel the transaction
        return super().delete(**kwargs)


class Withdrawal(TimeStampedModel):

    STATUSES = (
        ('awaiting transaction signature', 'awaiting transaction signature'),
        ('awaiting confirmation', 'awaiting confirmation'),
        ('finished', 'finished'),
        ('canceled', 'canceled'),
    )
    balance = models.ForeignKey(
        Balance,
        related_name='withdrawals',
        on_delete=models.CASCADE,
    )
    amount = models.DecimalField(
        max_digits=30,
        decimal_places=9,
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(2**64)]
    )
    status = models.CharField(max_length=255, choices=STATUSES)
    confirmations = models.IntegerField(
        validators=[MinValueValidator(0)],
        default=0
    )
    # tx_slate_id is needed in case when we want to cancel the withdrawal after
    # the first step of SRS (eg. when new withdrawal is initiated)
    tx_slate_id = models.CharField(unique=True, max_length=255)
    # we store kernel excess to update number of confirmations
    kernel_excess = models.CharField(
        unique=True, null=True, blank=True, max_length=255)

    class Meta:
        ordering = ['created']

    def __str__(self):
        return '{}, amount: {}, status: {}, user:{}'.format(
            self.balance.currency.symbol,
            self.amount,
            self.status,
            self.balance.user.username
        )

    @transaction.atomic
    def save(self, *args, **kwargs):
        """On withdrawal create set permissions"""
        created = self.pk is None
        if not created:
            current_withdrawal = Withdrawal.objects.get(pk=self.pk)
            if (
                current_withdrawal.status == 'awaiting transaction signature' and
                self.status == 'awaiting confirmation'
            ):
                # finished the transaction, lock amount in balance
                balance = self.balance
                balance.locked_amount = balance.locked_amount + self.amount
                balance.amount = balance.amount - self.amount
                balance.save()
            elif (
                self.status == 'awaiting confirmation' and
                self.confirmations == settings.REQUIRED_CONFIRMATIONS
            ):
                self.status = 'finished'
                # withdrawal completed, remove locked amount
                balance = self.balance
                balance.locked_amount = balance.locked_amount - self.amount
                balance.save()
        # full_clean runs validators
        self.full_clean()
        res = super().save(*args, **kwargs)

        if created:
            assign_perm('api.view_withdrawal', self.balance.user, self)
        return res

    @transaction.atomic
    def delete(self, **kwargs):
        # we need to remove locked amount from balance if anything is locked
        # NOTE: this can also be called on an already confirmed withdrawal in
        # which case nothing is locked
        if self.status == 'awaiting confirmation':
            # the withdrawal's amount is locked in its balance, return it to
            # the available balance
            balance = self.balance
            balance.locked_amount = balance.locked_amount - self.amount
            balance.amount = balance.amount + self.amount
            balance.save()
            # NOTE: we should cancel tx here, but it's more explicit to do it
            # in the view. The downside is that when we delete it through a
            # shell we need to manually cancel the transaction
        return super().delete(**kwargs)
