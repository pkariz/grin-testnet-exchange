<template>
  <v-row justify="center">
    <v-dialog
      v-model="dialog"
      persistent
      max-width="600"
    >
      <v-stepper v-model="currentStep">
        <v-stepper-header>
          <v-stepper-step
            :complete="currentStep > 1"
            step="1"
          >
            Paste contract
          </v-stepper-step>

          <v-divider></v-divider>

          <v-stepper-step
            :complete="currentStep > 2"
            step="2"
          >
            Sign contract
          </v-stepper-step>

          <v-divider></v-divider>

          <v-stepper-step
            :complete="validSlatepack"
            step="3"
          >
            Copy contract
          </v-stepper-step>
        </v-stepper-header>

        <v-stepper-items>
          <v-stepper-content step="1" class="pa-4">
            <!-- STEP 1: user pastes created contract -->
            <v-card
              class="mb-12"
              height="600px"
            >
            <v-card-text>
              <v-row class="text-center align-self-center justify-center" style="height: 600px" v-if="loading.verifyingSlatepack">
                <v-col cols="12" class="my-5" style="height: 50px">
                  <h2>Reading contract</h2>
                </v-col>
                <v-col style="height: 100%">
                <v-progress-circular
                  indeterminate
                  color="primary"
                  class="pt-0 text-center justify-center"
                ></v-progress-circular>
                </v-col>
              </v-row>
              <v-textarea
                v-else-if="!validSlatepack"
                id="slatepackmsg2"
                v-model="pastedSlatepackMsg"
                name="slatepack-msg-2"
                label="Paste transaction contract"
                class="pa-0"
                rows="8"
                @input="onSlatepackPaste"
                :loading="loading.verifyingSlatepack"
              ></v-textarea>
              <!--
              <v-row class="text-center align-self-center justify-center" style="height: 600px" v-else>
                <v-col cols="12" class="mt-5" style="height: 40px">
                  <h2>Transaction contract completed</h2>
                </v-col>
                <v-col cols="12">
                  <v-icon large color="primary">
                    mdi-check
                  </v-icon>
                </v-col>
                <v-col cols="12">
                  Please check your deposit history for on-chain confirmation. Once the transaction lands on the chain
                  and gets enough confirmations your grin balance on the exchange will be automatically credited.
                </v-col>
              </v-row>
              -->
            </v-card-text>
            </v-card>
            <v-btn
              v-if="!loading.verifyingSlatepack && validSlatepack"
              small
              tile
              color="primary"
              class="black--text"
              @click="$emit('close')"
            >
              Close
            </v-btn>
            <v-btn
              v-if="!validSlatepack"
              small
              tile
              text
              @click="$emit('close')"
            >
              Cancel
            </v-btn>
          </v-stepper-content>
          <v-stepper-content step="2" class="pa-4">
            <!-- STEP 2: view transaction contract and confirm -->
            <v-card
              class="mb-12"
              height="600px"
              v-if="currentStep === 2"
            >
            <v-card-text>
              <transaction-contract
                :step="2"
                :amount="decimalAmount"
                :payerAddress="contractData.payerAddress"
                :receiverAddress="contractData.receiverAddress"
                :message="contractData.message"
                :signatures="[...contractData.signatures]"
                :slatepack="pastedSlatepackMsg"
                @signed="$emit('deposit-complete')"
              ></transaction-contract>
            </v-card-text>
            </v-card>

            <v-btn small tile text class="mx-5" @click="$emit('close')">
              Cancel
            </v-btn>
          </v-stepper-content>
        </v-stepper-items>
      </v-stepper>
    </v-dialog>
  </v-row>
</template>
<script>
import { createNamespacedHelpers } from 'vuex'
import { copyToClipboard } from '@/shared/helpers';
import TransactionContract from '@/components/TransactionContract.vue';
import WalletService from '@/services/wallet';
import { Decimal } from 'decimal.js';

const { mapState } = createNamespacedHelpers('auth')

export default {
  name: 'DepositModal',
  components: {
    'transaction-contract': TransactionContract,
  },
  props: {
    dialog: Boolean,
  },
  data: () => ({
    contractData: {
      // amount is not a number, it's a result of calling .match on a number
      step: 2,
      amount: null,
      payerAddress: '',
      receiverAddress: String(process.env.VUE_APP_EXCHANGE_WALLET_ADDRESS),
      signatures: [],
      message: '',
      initialSlatepackMsg: null,
    },
    currentStep: 1,
    minAmount: new Decimal(0.1),
    pastedSlatepackMsg: null,
    validSlatepack: false,
    newSlatepack: null,
    loading: {
      step2: false,
      verifyingSlatepack: false,
    },
  }),
  created: function() {
    this.contractData.message = 'deposit grin user: ' + this.user().username;
  },
  computed: {
    decimalAmount() {
      return new Decimal(this.contractData.amount[0]);
    }
  },
  methods: {
    copySlatepackMsg: function() {
      copyToClipboard(this.newSlatepack);
      this.$toasted.show('Transaction contract copied!')
    },
    onSlatepackPaste () {
      if (this.pastedSlatepackMsg === '') {
        return;
      }
      this.loading.verifyingSlatepack = true;
      WalletService.startDeposit(
        'GRIN',
        this.pastedSlatepackMsg
      ).then(({ slate, slatepack }) => {
        if (slate.sta !== 'S1') {
          this.$toasted.error('Invalid slatepack');
          return;
        }
        setTimeout(() => {
          this.validSlatepack = true;
          this.contractData.payerAddress = slatepack.sender;
          this.contractData.amount = (slate.amt / 1000000000) + '';
          this.restrictDecimal();
          this.currentStep = 2;
          this.loading.verifyingSlatepack = false;
        }, 1000);
      }).catch(() => {
        this.$toasted.error('Failed to parse contract state.');
        this.loading.verifyingSlatepack = false;
      });
    },
    restrictDecimal () {
      this.contractData.amount = this.contractData.amount.match(/^\d+\.?\d{0,9}/);
    },
    moveToStep3 (newSlatepack) {
      this.newSlatepack = newSlatepack;
      this.currentStep = 3;
    },
    ...mapState([
      'user',
    ]),
  },
}
</script>
<style>
.v-stepper .v-stepper__step__step {
  color: black !important;
}
.v-stepper .v-stepper__step__step .v-icon {
  color: black !important;
}
</style>
