import { api } from '@/services/auth'
import { Decimal } from 'decimal.js';

export default {
  fetchBalances() {
    return api.get(`/api/balances/`)
      .then(response => {
        const balances = response.data;
        for (const balance of balances) {
          balance.amount = new Decimal(balance.amount);
          balance.locked_amount = new Decimal(balance.locked_amount);
        }
        return balances;
      })
  },
  fetchDeposits() {
    return api.get(`/api/deposits/`)
      .then(response => {
        const deposits = response.data;
        for (const deposit of deposits) {
          deposit.amount = new Decimal(deposit.amount);
        }
        return deposits;
      })
  },
  fetchWithdrawals() {
    return api.get(`/api/withdrawals/`)
      .then(response => {
        const withdrawals = response.data;
        for (const withdrawal of withdrawals) {
          withdrawal.amount = new Decimal(withdrawal.amount);
        }
        return withdrawals;
      })
  },
}
