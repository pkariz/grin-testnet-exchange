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
        slatepack_msg = request.data.pop('slatepack_msg', None)
        if not slatepack_msg:
            return Response(
                data={'detail': 'Invalid data'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            wallet_api = WalletV3.get_wallet_api()
            # get slatepack so that you get the sender's address
            slatepack = wallet_api.decode_slatepack_message(slatepack_msg, [0])
            # get slate so that you get amount etc
            slate = wallet_api.slate_from_slatepack_message(slatepack_msg, [0])
        except WalletError as e:
            logger.error('Failed to get slate or slatepack, e: {}'.format(str(e)))
            raise APIException('Failed to get slate from slatepack')
        if slate['sta'] != 'S1':
            return Response(
                data={'detail': 'Invalid contract.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            data={ 'slate': slate, 'slatepack': slatepack },
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

    def _remove_existing_deposit(self, symbol, user):
        wallet_api = WalletV3.get_wallet_api()
        # there could be a problem if tx has been broadcasted, but not yet mined
        # since we would still delete it - we don't care since it's a testing exchange
        existing_step1_deposit = Deposit.objects.filter(
            status="awaiting confirmation",
            confirmations=0,
            balance__currency__symbol='GRIN',
            balance__user=user
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

    def finish_deposit_grin(self, request):
        slatepack_msg = request.data.pop('slatepack_msg', None)
        if not slatepack_msg:
            return Response(
                data={'detail': 'Invalid data'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            # remove existing deposit if it exists
            self._remove_existing_deposit('GRIN', request.user)
            wallet_api = WalletV3.get_wallet_api()
            # get slatepack for sender's address
            slatepack = wallet_api.decode_slatepack_message(slatepack_msg, [0])
            # get slate for the amount and we need it to sign the contract
            slate = wallet_api.slate_from_slatepack_message(slatepack_msg, [0])
            user_wallet_address = slatepack['sender']
            amount = int(slate['amt'])
            # validate amount
            min_amount = 100000000  # 0.1 grin
            if amount < min_amount:
                return Response(
                    data={
                        'detail': 'Minimum amount is {0:f} grin'.format(min_amount/1000000000),
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            # sign the contract, this stores tx in wallet db. Don't do a payjoin, because
            # we don't count utxos and it's easier to have a problem if we do a payjoin here
            signed_slate = wallet_api.contract_sign(amount, slate, is_payjoin=False)
            # easier to revert exchange db tx than state in grin db
            deposit = Deposit.objects.create(
                tx_slate_id=slate['id'],
                amount=Decimal(str(amount)) / Decimal('1000000000'),
                confirmations=0,
                status="awaiting confirmation",
                balance=request.user.balances.get(currency__symbol='GRIN'),
            )
            new_slatepack_message = wallet_api.create_slatepack_message(
                signed_slate,
                [user_wallet_address],
                # we need to specify sender so that the returned slatepack will be
                # encrypted. Not sure whether 0 is always appropriate or not
                sender_index=0
            )
        except Exception as e:
            logger.error(str(e))
            raise APIException('Something went wrong')
        return Response(
            data= {
                'deposit' : DepositSerializer(deposit).data,
                'slatepack': new_slatepack_message,
            },
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
        slate = wallet_api.contract_new(
            int(-amount * Decimal('1000000000')),
            user_wallet_address,
            is_payjoin=False,
        )
        # delete any existing withdrawal instances for this user for grin
        existing_step1_withdrawal = Withdrawal.objects.filter(
            status="awaiting transaction signature",
            confirmations=0,
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
            tx_slate_id=slate['id'],
        )
        # now we create a slatepack message from the slate
        slatepack_message = wallet_api.create_slatepack_message(
            slate,
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
            amount = int(slate['amt'])
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
        if slate['sta'] != 'S2':
            return Response(
                data={'detail': 'Invalid contract.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            # finalize tx and push it
            final_slate = wallet_api.contract_sign(-amount, slate)
            wallet_api.post_tx(final_slate)
        except Exception as e:
            logger.exception('Failed to finalize or post the transaction, e: {}'.format(str(e)))
            raise APIException('Something went wrong')
        # update the withdrawal
        tx = wallet_api.retrieve_txs(
            tx_slate_id=final_slate['id'], refresh=True)[0]
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
