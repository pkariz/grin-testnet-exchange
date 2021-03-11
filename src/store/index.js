import Vue from 'vue'
import Vuex from 'vuex'
import auth from './modules/auth'
import balance from './modules/balance'
import createPersistedState from 'vuex-persistedstate';

Vue.use(Vuex)

export default new Vuex.Store({
  modules: {
    auth,
    balance,
  },
  plugins: [
    createPersistedState({
      paths: ['auth'],
    }),
  ],
})
