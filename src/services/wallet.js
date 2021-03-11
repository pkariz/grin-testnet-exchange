import { api } from '@/services/auth'

export default {
  startDeposit(symbol, address, amount, message) {
    return api.post(`/api/deposits/start/`, {symbol, address, amount, message})
      .then(response => response.data)
  },
  finishDeposit(symbol, data) {
    return api.post(`/api/deposits/finish/`, {symbol, data})
      .then(response => response.data)
  },
  startWithdrawal(symbol, address, amount, message) {
    return api.post(`/api/withdrawals/start/`, {symbol, address, amount, message})
      .then(response => response.data)
  },
  finishWithdrawal(symbol, data) {
    return api.post(`/api/withdrawals/finish/`, {symbol, data})
      .then(response => response.data)
  },
  fetchDeposits() {
    return api.get(`/api/deposits/`)
      .then(response => response.data)
  },
  fetchWithdrawals() {
    return api.get(`/api/withdrawals/`)
      .then(response => response.data)
  },
}
