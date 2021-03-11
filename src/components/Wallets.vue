<template>
  <v-container fluid class="pa-0 mx-0">
  <v-col cols="12">
    <v-data-table
      :headers="headers"
      :items="balances() || []"
      :loading="balances() === null"
      class="elevation-1 mb-5"
      hide-default-footer
      caption="Wallets"
    >
      <template v-slot:item.currency.name="{ item }">
        <v-col class="pa-0 px-3 flex-grow-0 flex-shrink-0">
          <v-img
            alt="[no logo]"
            :src="logos()[item.currency.symbol.toLowerCase()]"
            width="22"
          />
        </v-col>
      </template>
      <template v-slot:item.actions="{ item }">
        <v-btn small tile color="primary" class="btn-action black--text ml-5 my-3" @click="handleWithdraw(item.currency.symbol)">
          <v-icon>mdi-arrow-up-bold</v-icon>&nbsp;Withdraw
        </v-btn>
        <v-btn small tile color="primary" class="btn-action black--text ml-5 my-3" @click="handleDeposit(item.currency.symbol)">
          <v-icon>mdi-arrow-down-bold</v-icon>&nbsp;Deposit
        </v-btn>
      </template>
    </v-data-table>
    <deposit-modal
      :dialog="dialogDeposit"
      :key="`d-${dialogDepositKey}`"
      @close="closeDialogDeposit"
      @deposit-complete="$emit('changed')"
    ></deposit-modal>
    <withdrawal-modal
      :dialog="dialogWithdrawal"
      :key="`w-${dialogWithdrawalKey}`"
      @close="closeDialogWithdrawal"
      @withdrawal-complete="$emit('changed')"
    ></withdrawal-modal>
  </v-col>
  </v-container>
</template>

<script>
import { createNamespacedHelpers } from 'vuex'
import DepositModal from '@/components/DepositModal.vue'
import WithdrawalModal from '@/components/WithdrawalModal.vue'

const { mapState, mapGetters, mapActions } = createNamespacedHelpers('balance')

export default {
  name: 'Wallets',
  components: {
    'deposit-modal': DepositModal,
    'withdrawal-modal': WithdrawalModal,
  },
  data: () => ({
    headers: [
      { text: 'Currency', align: 'left', value: 'currency.name' },
      { text: 'Symbol', value: 'currency.symbol' },
      { text: 'Balance', value: 'amount' },
      { text: 'Locked balance', value: 'locked_amount' },
      { text: 'Actions', align: 'center', value: 'actions', sortable: false },
    ],
    dialogDeposit: false,
    dialogWithdrawal: false,
    dialogDepositKey: 1,
    dialogWithdrawalKey: 1,
  }),
  created: function() {
    this.getBalances()
      .catch(() => {
        this.$toasted.error('Failed to fetch balances');
      });
  },
  methods: {
    handleWithdraw: function(symbol) {
      this.dialogWithdrawal = true;
    },
    handleDeposit: function(symbol) {
      this.dialogDeposit = true;
    },
    closeDialogDeposit: function() {
      this.dialogDeposit = false;
      this.dialogDepositKey++;
    },
    closeDialogWithdrawal: function() {
      this.dialogWithdrawal = false;
      this.dialogWithdrawalKey++;
    },
    ...mapState([
      'logos',
    ]),
    ...mapGetters([
      'balances',
    ]),
    ...mapActions([
      'getBalances',
    ]),
  },
}
</script>
<style scoped>
.btn-action {
  width: 125px;
}

>>>.v-data-table caption {
  margin-top: 10px;
  margin-bottom: 20px;
  font-weight: 500;
  font-size: x-large;
}
</style>
