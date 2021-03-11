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
            Amount
          </v-stepper-step>

          <v-divider></v-divider>

          <v-stepper-step
            :complete="currentStep > 2"
            step="2"
          >
            Transaction contract
          </v-stepper-step>

          <v-divider></v-divider>

          <v-stepper-step
            :complete="validSlatepack"
            step="3"
          >
            Signature
          </v-stepper-step>
        </v-stepper-header>

        <v-stepper-items>
          <v-stepper-content step="1" class="pa-4">
            <!-- STEP 1: pick amount to deposit -->
            <v-card
              class="mb-12"
              height="600px"
            >
            <v-card-text>
              <h2 class="my-5">
                Please enter the amount of grin you wish to deposit and your wallet address.
                Both are needed to generate a transaction contract.
              </h2>
              <ValidationObserver
                v-slot="{ invalid, validated, handleSubmit }"
              >
                <ValidationProvider
                  name="amount"
                  rules="required|min_value:0.1"
                  v-slot="{ errors }"
                >
                  <v-text-field
                    v-model="contractData.amount"
                    type="number"
                    label="Deposit amount"
                    :error-messages="errors"
                    @input="restrictDecimal"
                  />
                </ValidationProvider>
                <ValidationProvider
                  name="address"
                  rules="required"
                  v-slot="{ errors }"
                >
                  <v-text-field
                    v-model="contractData.thirdPartyAddress"
                    label="Wallet address"
                    :error-messages="errors"
                    hint="Enter your wallet address"
                    persistent-hint
                  />
                </ValidationProvider>
                <v-textarea
                  v-model="contractData.message"
                  name="message"
                  label="Message"
                  rows="4"
                  class="mt-5"
                  disabled
                ></v-textarea>
              </ValidationObserver>
            </v-card-text>
            </v-card>

            <v-btn
              small
              tile
              color="primary"
              class="black--text"
              @click="moveToStep2"
              :disabled="contractData.amount < minAmount || contractData.thirdPartyAddress === ''"
              :loading="loading.step2"
            >
              Continue
            </v-btn>

            <v-btn small tile text class="mx-5" @click="$emit('close')">
              Cancel
            </v-btn>
          </v-stepper-content>

          <v-stepper-content step="2" class="pa-4">
            <!-- STEP 2: copy transaction contract -->
            <v-card
              class="mb-12"
              height="600px"
              v-if="currentStep > 1"
            >
            <v-card-text>
              <transaction-contract
                :txType="contractData.txType"
                :ownerInitiated="contractData.ownerInitiated"
                :nrParticipants="contractData.nrParticipants"
                :amount="decimalAmount"
                :ownerAddress="contractData.ownerAddress"
                :thirdPartyAddress="contractData.thirdPartyAddress"
                :message="contractData.message"
                :signatures="[...contractData.signatures]"
                :slatepackMsgToCopy="contractData.initialSlatepackMsg"
              ></transaction-contract>
            </v-card-text>
            </v-card>

            <v-btn
              small
              tile
              color="primary"
              class="black--text"
              @click="currentStep = 3"
            >
              Continue
            </v-btn>

            <v-btn small tile text class="mx-5" @click="$emit('close')">
              Cancel
            </v-btn>
          </v-stepper-content>

          <v-stepper-content step="3" class="pa-4">
            <!-- STEP 3: paste signed contract -->
            <v-card
              class="mb-12"
              height="600px"
              v-if="currentStep > 2"
            >
            <v-card-text>
              <v-row class="text-center align-self-center justify-center" style="height: 600px" v-if="loading.verifyingSlatepack">
                <v-col cols="12" class="my-5" style="height: 50px">
                  <h2>Completing transaction contract</h2>
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
                v-model="signedSlatepackMsg"
                name="slatepack-msg-2"
                label="Paste signed transaction contract"
                class="pa-0"
                rows="8"
                @input="onSlatepackPaste"
                :loading="loading.verifyingSlatepack"
              ></v-textarea>
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
      txType: 'invoice',
      ownerInitiated: true,
      nrParticipants: 2,
      // amount is not a number, it's a result of calling .match on a number
      amount: null,
      thirdPartyAddress: '',
      ownerAddress: String(process.env.VUE_APP_EXCHANGE_WALLET_ADDRESS),
      signatures: [],
      message: null,
      initialSlatepackMsg: null,
    },
    currentStep: 1,
    minAmount: new Decimal(0.1),
    signedSlatepackMsg: null,
    validSlatepack: false,
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
      copyToClipboard(this.slatepackMsg);
      this.$toasted.show('Transaction contract copied!')
    },
    onSlatepackPaste () {
      this.loading.verifyingSlatepack = true;
      WalletService.finishDeposit(
        'GRIN',
        { 'slatepack_msg': this.signedSlatepackMsg }
      ).then(() => {
        this.validSlatepack = true;
        this.$emit('deposit-complete');
      }).catch(() => {
        this.$toasted.error('Transaction finalization failed');
      }).finally(() => {
        this.loading.verifyingSlatepack = false;
      });
    },
    restrictDecimal () {
      this.contractData.amount = this.contractData.amount.match(/^\d+\.?\d{0,9}/);
    },
    moveToStep2 () {
      this.loading.step2 = true;
      WalletService.startDeposit(
        'GRIN',
        this.contractData.thirdPartyAddress,
        new Decimal(this.contractData.amount[0]),
        this.contractData.message
      ).then((slatepackMsg) => {
        this.contractData.initialSlatepackMsg = slatepackMsg;
        this.currentStep = 2;
      }).catch((error) => {
        this.$toasted.error(error.response.data.detail);
      }).finally(() => {
        this.loading.step2 = false;
      });
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
