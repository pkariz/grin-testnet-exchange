from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.views.generic import TemplateView
from django.views.decorators.cache import never_cache
from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.response import Response
from decimal import Decimal

from .serializers import (
    UserSerializer,
    BalanceSerializer,
    CurrencySerializer,
    DepositSerializer,
    WithdrawalSerializer,
)
from .models import Balance, Currency, Deposit, Withdrawal
from .mixins import AllowAnyRetrieveAndListMixin, CustomModelViewSet
from .permissions import ObjectPermissions
from .wallet import WalletV3, WalletError

import logging

logger = logging.getLogger(__name__)


# Serve Vue Application
index_view = never_cache(TemplateView.as_view(template_name='index.html'))


class UserCreate(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny, )


class BalanceViewSet(CustomModelViewSet):
    """API endpoint for getting balances"""
    queryset = Balance.objects.all()
    serializer_class = BalanceSerializer


class CurrencyViewSet(AllowAnyRetrieveAndListMixin, CustomModelViewSet):
    """API endpoint for getting currencies"""
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer


class DepositViewSet(CustomModelViewSet):
    """API endpoint for getting deposits"""
    queryset = Deposit.objects.filter(~Q(status="awaiting transaction signature"))
    serializer_class = DepositSerializer

    @transaction.atomic
    @action(
        detail=False,
        methods=['post'],
        url_path='start',
        url_name='start',
    )
    def start_deposit(self, request):
        currency_symbol = request.data.pop('symbol')
        if currency_symbol.lower() == 'grin':
            return self.start_deposit_grin(request)
        else:
            raise APIException('Deposit not supported')

    def start_deposit_grin(self, request):
        user_wallet_address = request.data.pop('address', None)
        amount = request.data.pop('amount')
        if not user_wallet_address or not amount:
            return Response(
                data={'detail': 'Invalid data'},
                status=status.HTTP_400_BAD_REQUEST
            )
        amount = Decimal(str(amount))
        min_amount = Decimal('0.1')
        if amount < min_amount:
            return Response(
                data={'detail': 'Minimum amount is {0:f} grin'.format(min_amount)},
                status=status.HTTP_400_BAD_REQUEST
            )
        wallet_api = WalletV3.get_wallet_api()
        # exchange has more control if it finalizes, so we need to create a RSR
        # when we do a deposit.

        # NOTE: wallet api 'issue_invoice_tx' is still missing some arguments,
        # eg: late_lock etc ('init_send_tx' has that already), although in the
        # future late_lock should probably be the default (and only) way
        try:
            versioned_slate = wallet_api.issue_invoice_tx({
                # NOTE: amount for api is in nanogrin, that's why we multiply
                'amount': str(int(amount * Decimal('1000000000'))),
            })
        except WalletError as e:
            logger.error('issue_invoice_tx failed, user: {}, amount: {}'.format(
                request.user.username, amount))
            raise APIException('Failed to create an invoice')
            
        # versioned_slate data is something like: {
        #   "amt": "6000000000",
        #   "id": "0436430c-2b02-624c-2032-570501212b00",
        #   "sigs": [
        #      {
        #        "nonce": "031b84c5567b126440995d3ed5aaba0565d71e1834604819ff9c17f5e9d5dd078f",
        #        "xs": "02e89cce4499ac1e9bb498dab9e3fab93cc40cd3d26c04a0292e00f4bf272499ec"
        #      }
        #   ],
        #   "sta": "I1",
        #   "ver": "4:2"
        # }

        # delete any existing deposit instances for this user for grin
        # NOTE: we could just change its status to canceled or smth
        existing_step1_deposit = Deposit.objects.filter(
            status="awaiting transaction signature",
            balance__currency__symbol='GRIN',
            balance__user=request.user
        ).first()
        if existing_step1_deposit:
            # cancel the transaction of previous unfinished deposit
            try:
                wallet_api.cancel_tx(tx_slate_id=existing_step1_deposit.tx_slate_id)
            except Exception as e:
                # who knows why this can fail, maybe they've manually deleted it
                # before
                pass
            # delete the instance
            existing_step1_deposit.delete()
        # create a deposit instance
        balance = self.request.user.balances.get(
            currency__symbol='GRIN')
        deposit = Deposit.objects.create(
            balance=balance,
            amount=amount,
            confirmations=0,
            status='awaiting transaction signature',
            tx_slate_id=versioned_slate['id'],
        )
        # now we create a slatepack message from the slate
        slatepack_message = wallet_api.create_slatepack_message(
            versioned_slate,
            [user_wallet_address],
            # we need to specify sender so that the returned slatepack will be
            # encrypted. Not sure whether 0 is always appropriate or not
            sender_index=0
        )
        return Response(
            data=slatepack_message,
            status=status.HTTP_200_OK
        )

    @transaction.atomic
    @action(
        detail=False,
        methods=['post'],
        url_path='finish',
        url_name='finish',
    )
    def finish_deposit(self, request):
        currency_symbol = request.data.pop('symbol')
        if currency_symbol.lower() == 'grin':
            return self.finish_deposit_grin(request)
        else:
            raise APIException('Deposit not supported')

    def finish_deposit_grin(self, request):
        try:
            slatepack_msg = request.data.pop('data')['slatepack_msg']
            if slatepack_msg is None:
                raise Exception()
        except:
            return Response(
                data={'detail': 'Invalid data'},
                status=status.HTTP_400_BAD_REQUEST
            )
        wallet_api = WalletV3.get_wallet_api()
        # decode slatepack message and find the matching deposit
        # NOTE: if deposit exists then tx in db for it also exists, unless db
        # is corrupted
        try:
            slate = wallet_api.slate_from_slatepack_message(slatepack_msg, [0])
            deposit = Deposit.objects.get(
                tx_slate_id=slate['id'],
                status="awaiting transaction signature",
                balance__currency__symbol='GRIN',
                balance__user=request.user
            )
        except:
            return Response(
                data={'detail': 'Only the latest given deposit contract is valid.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        # we will call finalize, we want to finalize invoice, not payment
        if slate['sta'] != 'I2':
            return Response(
                data={'detail': 'Invalid contract.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            # finalize tx and push it
            final_slate = wallet_api.finalize_tx(slate)
            wallet_api.post_tx(final_slate)
        except Exception as e:
            logger.exception('Failed to finalize or post the transaction')
            raise APIException('Something went wrong')
        # update the deposit
        tx = wallet_api.retrieve_txs(
            tx_slate_id=final_slate['id'], refresh=False)[0]
        deposit.status = 'awaiting confirmation'
        deposit.kernel_excess = tx['kernel_excess']
        deposit.save()
        return Response(
            data=DepositSerializer(deposit).data,
            status=status.HTTP_200_OK
        )

    def get_permissions(self):
        """
        Add/delete/update requests require isAdminUser, list/retrieve/ requests
        require view_deposit object permission, start_deposit/finish_deposit
        require only IsAuthenticated permission.
        """
        permission_classes = [IsAuthenticated]
        if self.action not in ['list', 'retrieve']:
            permission_classes.append(ObjectPermissions)
        if self.action in ['destroy', 'create', 'update', 'partial_update']:
            permission_classes.append(IsAdminUser)
        return [permission() for permission in permission_classes]


class WithdrawalViewSet(CustomModelViewSet):
    """API endpoint for getting withdrawals"""
    queryset = Withdrawal.objects.filter(
        ~Q(status="awaiting transaction signature"))
    serializer_class = WithdrawalSerializer

    @transaction.atomic
    @action(
        detail=False,
        methods=['post'],
        url_path='start',
        url_name='start',
    )
    def start_withdrawal(self, request):
        currency_symbol = request.data.pop('symbol')
        if currency_symbol.lower() == 'grin':
            return self.start_withdrawal_grin(request)
        else:
            raise APIException('Withdrawal not supported')

    def start_withdrawal_grin(self, request):
        user_wallet_address = request.data.pop('address', None)
        amount = request.data.pop('amount')
        if not user_wallet_address or not amount:
            return Response(
                data={'detail': 'Invalid data'},
                status=status.HTTP_400_BAD_REQUEST
            )
        amount = Decimal(str(amount))
        min_amount = Decimal('0.1')
        if amount < min_amount:
            return Response(
                data={'detail': 'Minimum amount is {0:f} grin'.format(min_amount)},
                status=status.HTTP_400_BAD_REQUEST
            )
        balance = request.user.balances.get(currency__symbol='GRIN')
        if amount > balance.amount:
            return Response(
                data={
                    'detail': "Your balance only has {0:f} grin".format(
                        balance.amount)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        wallet_api = WalletV3.get_wallet_api()
        # exchange has more control if it finalizes, so we need to create a SRS
        # when we do a withdrawal. We also want to use late-locking for obvious
        # reasons
        versioned_slate = wallet_api.init_send_tx({
            # NOTE: amount for api is in nanogrin, that's why we multiply
            'amount': str(int(amount * Decimal('1000000000'))),
            # reorgs of 1 are normal, 2 rare, 3 seems safe
            'minimum_confirmations': 3,
            # selection_strategy_is_use_all is false because exchanges can't
            # work with this set to true, as they would quickly run out of utxos
            'selection_strategy_is_use_all': False,
            # num_change_outputs is optional, but we should probably define it,
            # we could even make it dependent on the amount
            'num_change_outputs': 1,
            # we want payment proof
            'payment_proof_recipient_address': user_wallet_address,
            # we want late-locking, otherwise user's can spam-lock exchange's
            # utxos, when late-locking is default, we can remove this
            'late_lock': False,
            # max_outputs is required
            'max_outputs': 500,
        })
        # versioned_slate data is something like: {
        #   'amt': '100000000',
        #   'fee': '23500000',
        #   'id': '540f5f75-7802-4778-909f-85c244bfb6f3',
        #   'proof': {
        #     'raddr': '3be4bb5011fd02e429fae4baefb9c3365bcf65800eb312d6390037fc84aa3e4b',
        #     'saddr': '641ac95c8c50c13c1c2e7a0adf756638a2ae028a1e992b157fbe97bb24df38ad'
        #   },
        #   'sigs': [
        #     {
        #       'nonce': '02c038fb179019bc6dfffeca6d6e0fd067f74aa9455c09261459afe721bc0db1b2',
        #       'xs': '02df98e2e4df377523fffbe936bb239582f565783fe709142e22aa3278a879acb5'
        #     }
        #   ],
        #   'sta': 'S1',
        #   'ver': '4:3'
        # }
        # delete any existing withdrawal instances for this user for grin
        existing_step1_withdrawal = Withdrawal.objects.filter(
            status="awaiting transaction signature",
            balance__currency__symbol='GRIN',
            balance__user=request.user
        ).first()
        if existing_step1_withdrawal:
            # cancel the transaction of previous unfinished withdrawal
            try:
                wallet_api.cancel_tx(tx_slate_id=existing_step1_withdrawal.tx_slate_id)
            except Exception as e:
                # who knows why this can fail, maybe they've manually deleted it
                # before
                pass
            # delete the instance, this will also unlock the locked amount
            existing_step1_withdrawal.delete()
        # create a withdrawal instance
        balance = self.request.user.balances.get(
            currency__symbol='GRIN')
        withdrawal = Withdrawal.objects.create(
            balance=balance,
            amount=amount,
            confirmations=0,
            status='awaiting transaction signature',
            tx_slate_id=versioned_slate['id'],
        )
        # now we create a slatepack message from the slate
        slatepack_message = wallet_api.create_slatepack_message(
            versioned_slate,
            [user_wallet_address],
            sender_index=0  # not sure that's correct, we need it for encryption
        )
        return Response(
            data=slatepack_message,
            status=status.HTTP_200_OK
        )

    @transaction.atomic
    @action(
        detail=False,
        methods=['post'],
        url_path='finish',
        url_name='finish',
    )
    def finish_withdrawal(self, request):
        currency_symbol = request.data.pop('symbol')
        if currency_symbol.lower() == 'grin':
            return self.finish_withdrawal_grin(request)
        else:
            raise APIException('Withdrawal not supported')

    def finish_withdrawal_grin(self, request):
        try:
            slatepack_msg = request.data.pop('data')['slatepack_msg']
            if slatepack_msg is None:
                raise Exception()
        except:
            return Response(
                data={'detail': 'Invalid data'},
                status=status.HTTP_400_BAD_REQUEST
            )
        wallet_api = WalletV3.get_wallet_api()
        # decode slatepack message and find the matching withdrawal
        # NOTE: if withdrawal exists then tx in db for it also exists
        try:
            slate = wallet_api.slate_from_slatepack_message(slatepack_msg, [0])
            withdrawal = Withdrawal.objects.get(
                tx_slate_id=slate['id'],
                status="awaiting transaction signature",
                balance__currency__symbol='GRIN',
                balance__user=request.user
            )
        except:
            return Response(
                data={'detail': 'Only the latest given Withdrawal contract is valid.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        # we will call finalize, we want to finalize payment, not invoice
        if slate['sta'] != 'S2':
            return Response(
                data={'detail': 'Invalid contract.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            # finalize tx and push it
            final_slate = wallet_api.finalize_tx(slate)
            wallet_api.post_tx(final_slate)
        except Exception as e:
            logger.exception('Failed to finalize or post the transaction')
            raise APIException('Something went wrong')
        # update the withdrawal
        tx = wallet_api.retrieve_txs(
            tx_slate_id=final_slate['id'], refresh=False)[0]
        withdrawal.status = 'awaiting confirmation'
        withdrawal.kernel_excess = tx['kernel_excess']
        withdrawal.save()
        return Response(
            data=WithdrawalSerializer(withdrawal).data,
            status=status.HTTP_200_OK
        )

    def get_permissions(self):
        """
        Add/delete/update requests require isAdminUser, list/retrieve/ requests
        require view_withdrawal object permission, start_withdrawal and
        finish_withdrawal require only IsAuthenticated permission.
        """
        permission_classes = [IsAuthenticated]
        if self.action not in ['list', 'retrieve']:
            permission_classes.append(ObjectPermissions)
        if self.action in ['destroy', 'create', 'update', 'partial_update']:
            permission_classes.append(IsAdminUser)
        return [permission() for permission in permission_classes]
