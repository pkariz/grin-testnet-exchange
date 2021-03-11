import balanceService from '../../services/balance'

const state = {
  balances: null,
  logos: {
    'grin': 'https://aws1.discourse-cdn.com/standard10/uploads/grin/original/1X/f96e1cdce64456785297c317e6cb84f3fab2edcb.svg',
    'btc': 'https://i.pinimg.com/originals/eb/be/b0/ebbeb0a28d38fe77ad5d7d6e13784217.png',
  },
  deposits: null,
  withdrawals: null,
}

const getters = {
  balances: state => {
    return state.balances
  },
  deposits: state => {
    return state.deposits
  },
  withdrawals: state => {
    return state.withdrawals
  },
}

const actions = {
  getBalances ({ commit }) {
    return balanceService.fetchBalances()
      .then(balances => {
        commit('setBalances', balances)
      })
  },
  getDeposits ({ commit }) {
    return balanceService.fetchDeposits()
      .then(deposits => {
        commit('setDeposits', deposits)
      })
  },
  getWithdrawals ({ commit }) {
    balanceService.fetchWithdrawals()
      .then(withdrawals => {
        commit('setWithdrawals', withdrawals)
      })
  },
}

const mutations = {
  setBalances (state, balances) {
    state.balances = balances
  },
  setDeposits (state, deposits) {
    state.deposits = deposits
  },
  addDeposit (state, deposit) {
    state.deposits.push(deposit)
  },
  setWithdrawals (state, withdrawals) {
    state.withdrawals = withdrawals
  },
  addWithdrawal (state, withdrawal) {
    state.withdrawals.push(withdrawal)
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}
