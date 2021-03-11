<template>
  <v-col cols="12">
    <v-data-table
      :headers="headers"
      :items="withdrawals() || []"
      :loading="withdrawals() === null"
      class="elevation-1"
      hide-default-footer
      caption="Withdrawals"
    >
      <template v-slot:item.balance.currency.name="{ item }">
        <v-col class="pa-0 px-3 flex-grow-0 flex-shrink-0">
          <v-img
            alt="[no logo]"
            :src="logos()[item.balance.currency.symbol.toLowerCase()]"
            width="22"
          />
        </v-col>
      </template>
      <template v-slot:item.created="{ item }">
        {{ formatDate(item.created) }}
      </template>
      <template v-slot:item.confirmations="{ item }">
          {{ item.confirmations }}/{{ neededConfirmations }}
      </template>
    </v-data-table>
  </v-col>
</template>

<script>
import { createNamespacedHelpers } from 'vuex'
import moment from 'moment';

const { mapState, mapGetters, mapActions } = createNamespacedHelpers('balance')

export default {
  name: 'Withdrawals',
  data: () => ({
    headers: [
      { text: 'Currency', align: 'left', value: 'balance.currency.name', width: '10%' },
      { text: 'Symbol', value: 'balance.currency.symbol', width: '20%' },
      { text: 'Balance', value: 'amount', width: '20%' },
      { text: 'Date', value: 'created', width: '20%' },
      { text: 'Confirmations', value: 'confirmations', width: '10%' },
      { text: 'Status', value: 'status', width: '20%' },
    ],
    neededConfirmations: 10,
  }),
  methods: {
    formatDate(value){
       if (value) {
         return moment(String(value)).format('DD/MM/YYYY HH:mm')
        }
    },
    ...mapState([
      'logos',
    ]),
    ...mapGetters([
      'withdrawals',
    ]),
    ...mapActions([
      'getWithdrawals',
    ]),
  },
}
</script>
<style scoped>
>>>.v-data-table caption {
  margin-top: 10px;
  margin-bottom: 20px;
  font-weight: 500;
  font-size: x-large;
}
</style>
