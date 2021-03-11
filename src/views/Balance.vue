<template>
  <v-container style="margin-top: 20px;">
    <v-row justify="center">
      <wallets class="mb-5" @changed="fetchStates"></wallets>
      <deposits></deposits>
      <withdrawals></withdrawals>
    </v-row>
  </v-container>
</template>

<script>
import { createNamespacedHelpers } from 'vuex'
import Wallets from '@/components/Wallets.vue'
import Deposits from '@/components/Deposits.vue'
import Withdrawals from '@/components/Withdrawals.vue'
const { mapActions } = createNamespacedHelpers('balance')

export default {
  name: 'Home',
  components: {
    'wallets': Wallets,
    'deposits': Deposits,
    'withdrawals': Withdrawals,
  },
  data: () => ({
    timeoutReference: null,
    refreshDelay: 1000*15,
  }),
  created: function() {
    this.fetchStates();
  },
  destroyed: function() {
    clearTimeout(this.timeoutReference);
  },
  methods: {
    fetchStates: function() {
      if (this.timeoutReference) {
        clearTimeout(this.timeoutReference);
      }
      this.fetchBalances();
      this.fetchDeposits();
      this.fetchWithdrawals();
      this.timeoutReference = setTimeout(this.fetchStates, this.refreshDelay);
    },
    fetchDeposits: function() {
      this.getDeposits()
        .catch(() => {
          this.$toasted.error('Failed to fetch deposits');
        });
    },
    fetchWithdrawals: function() {
      this.getWithdrawals()
        .catch(() => {
          this.$toasted.error('Failed to fetch withdrawals');
        });
    },
    fetchBalances: function() {
      this.getBalances()
        .catch(() => {
          this.$toasted.error('Failed to fetch balances');
        });
    },
    ...mapActions([
      'getBalances',
      'getDeposits',
      'getWithdrawals',
    ]),
  },
}
</script>
