from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from backend.api.models import Currency, Balance
from backend.api.helpers import assign_default_model_permissions
from decimal import Decimal
from guardian.shortcuts import assign_perm


def create_balances_for_user(user):
    for currency in Currency.objects.all():
        balance = Balance.objects.create(
            currency=currency,
            user=user,
            amount=Decimal(0),
            locked_amount=Decimal(0)
        )
        assign_perm('api.view_balance', user, balance)


def create_balances_for_currency(currency):
    for user in User.objects.all():
        balance = Balance.objects.create(
            currency=currency,
            user=user,
            amount=Decimal(0),
            locked_amount=Decimal(0)
        )
        assign_perm('api.view_balance', user, balance)


@receiver(
    post_save,
    sender=User,
    dispatch_uid="create_balances_for_new_user",
)
def on_user_create(sender, instance, created, **kwargs):
    # NOTE: anonymous check is for the first migrate which creates AnonymousUser
    # when permissions don't exist yet
    if created and instance.get_anonymous() != instance:
        assign_default_model_permissions(instance)
        create_balances_for_user(instance)


@receiver(
    post_save,
    sender=Currency,
    dispatch_uid="create_balances_for_new_currency",
)
def on_currency_create(sender, instance, created, **kwargs):
    if created:
        create_balances_for_currency(instance)
