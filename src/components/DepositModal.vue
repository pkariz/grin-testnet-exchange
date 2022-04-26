<template>
  <v-row justify="center">
    <v-dialog
      v-model="dialog"
      persistent
      max-width="800"
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
            :complete="copied"
            step="2"
          >
            Sign and copy contract
          </v-stepper-step>

        </v-stepper-header>

        <v-stepper-items>
          <v-stepper-content step="1" class="pa-4">
            <!-- STEP 1: user pastes created contract -->
            <v-card
              class="mb-6"
              height="700px"
            >
            <v-card-text>
              <v-row class="text-center align-self-center justify-center" style="height: 700px" v-if="loading.verifyingSlatepack">
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
              <template v-else-if="!validSlatepack">
              <p>
                Paste the result of running a grin-rust cli command (enter your own amount in it):<br>
                <strong>./grin-wallet --testnet contract new --send=&lt;amount&gt; --encrypt-for= tgrin1vsdvj...fxl8zksg7u4ut</strong>&nbsp;&nbsp;
                <v-fab-transition>
                  <v-icon v-if="cmdCopied" color="yellow">mdi-check</v-icon>
                  <v-icon v-else @click="copyCmd('./grin-wallet --testnet contract new --send=<amount> --encrypt-for=tgrin1vsdvjhyv2rqnc8pw0g9d7atx8z32uq52r6vjk9tlh6tmkfxl8zksg7u4ut')">
                    mdi-content-copy
                  </v-icon>
                </v-fab-transition>
              </p>
              <br>
              <v-textarea
                id="slatepackmsg2"
                v-model="pastedSlatepackMsg"
                name="slatepack-msg-2"
                label="Paste transaction contract"
                class="pa-0"
                rows="8"
                @input="onSlatepackPaste"
                :loading="loading.verifyingSlatepack"
              ></v-textarea>
              </template>
            </v-card-text>
            </v-card>
            <v-btn
              v-if="!loading.verifyingSlatepack && validSlatepack"
              tile
              color="primary"
              class="black--text mx-5"
              @click="$emit('close')"
            >
              Close
            </v-btn>
            <v-btn
              v-if="!validSlatepack"
              tile
              text
              class="mx-5"
              @click="$emit('close')"
            >
              Cancel
            </v-btn>
          </v-stepper-content>
          <v-stepper-content step="2" class="pa-4">
            <!-- STEP 2: view transaction contract and confirm -->
            <v-card
              class="mb-6"
              height="700px"
              v-if="currentStep === 2"
            >
            <v-card-text>
              <transaction-contract
                :step="2"
                :amount="decimalAmount"
                :payerAddress="contractData.payerAddress"
                :receiverAddress="contractData.receiverAddress"
                :message="contractData.message"
                :signatures="contractData.signatures"
                :slatepack="pastedSlatepackMsg"
                :autoSign="true"
                @signed="$emit('deposit-complete')"
                @copied="copied=true"
              ></transaction-contract>
            </v-card-text>
            </v-card>

            <v-btn tile text class="mx-5" @click="$emit('close')">
              {{ copied ? 'Close' : 'Cancel' }}
            </v-btn>
          </v-stepper-content>
        </v-stepper-items>
      </v-stepper>
    </v-dialog>
  </v-row>
</template>
<script>
import { createNamespacedHelpers } from 'vuex'
import TransactionContract from '@/components/TransactionContract.vue';
import WalletService from '@/services/wallet';
import { copyToClipboard } from '@/shared/helpers';
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
    copied: false,
    cmdCopied: false,
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
    copyCmd: function(cmd) {
      copyToClipboard(cmd);
      this.cmdCopied = true;
      setTimeout(() => {
        this.cmdCopied = false;
      }, 2000);
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
