from datetime import datetime, timedelta, timezone
from django.conf import settings
from .models import Deposit, Withdrawal
from .node import NodeV2API
from .wallet import WalletV3, WalletError

import dramatiq
import logging

logger = logging.getLogger(__name__)


# NOTE: django-dramatiq auto-discovers tasks in app/tasks.py
@dramatiq.actor
def update_deposits_and_withdrawals():
    node_api = NodeV2API()
    current_height = node_api.get_tip()['height']
    deposits = list(Deposit.objects.filter(
        confirmations__lt=settings.REQUIRED_CONFIRMATIONS,
        status="awaiting confirmation"
    ))
    withdrawals = list(Withdrawal.objects.filter(
        confirmations__lt=settings.REQUIRED_CONFIRMATIONS,
        status="awaiting confirmation"
    ))
    # we initialize it here, just so that we don't need to set it multiple times
    # later if it turns out that multiple transactions need to be re-broadcasted
    wallet_api = WalletV3.get_wallet_api()
    for deposit_or_withdrawal in deposits + withdrawals:
        if not deposit_or_withdrawal.kernel_excess:
            # we don't have the kernel_excess yet, retrieve tx so that we get its kernel
            # if it's confirmed
            try:
                tx = wallet_api.retrieve_txs(tx_slate_id=deposit_or_withdrawal.tx_slate_id, refresh=False)[0]
            except (KeyError, WalletError) as e:
                logger.error('Failed to retrieve tx in update_deposits_and_withdrawals, tx_slate_id: {}, e: {}'.format(
                    deposit_or_withdrawal.tx_slate_id, str(e)))
            if tx['confirmation_ts']:
                logger.info('updating kernel from {} to {}'.format(deposit_or_withdrawal.kernel_excess, tx['kernel_excess']))
                deposit_or_withdrawal.kernel_excess = tx['kernel_excess']
                deposit_or_withdrawal.save()
        if not deposit_or_withdrawal.kernel_excess:
            continue
        try:
            kernel_excess_height = node_api.get_kernel(
                deposit_or_withdrawal.kernel_excess,
                current_height - 60*24*7  # one week old max, speeds the search
            )['height']
        except KeyError:
            # kernel is not yet on the chain. It could be that it was just
            # created and has not been mined yet or transaction broadcast didn't
            # go through for some reason.
            continue
        if kernel_excess_height > current_height:
            # race condition, new block came between node calls, pretend you
            # fetched before we got this new block, otherwise number of
            # confirmations from different txs might not make sense
            continue
        else:
            new_confirmations = min(
                current_height - kernel_excess_height + 1, 10)
        deposit_or_withdrawal.confirmations = new_confirmations
        deposit_or_withdrawal.save()
