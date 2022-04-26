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
            Amount
          </v-stepper-step>

          <v-divider></v-divider>

          <v-stepper-step
            :complete="complete"
            step="2"
          >
            Copy &#38; sign contract
          </v-stepper-step>
        </v-stepper-header>

        <v-stepper-items>
          <v-stepper-content step="1" class="pa-4">
            <!-- STEP 1: pick amount to withdraw -->
            <v-card
              class="mb-12"
              height="700px"
            >
            <v-card-text>
              <h2 class="my-5">
                Please enter the amount of grin you wish to withdraw and your wallet address.
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
                    label="Withdraw amount"
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
                    v-model="contractData.receiverAddress"
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
                  rows="2"
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
              :disabled="contractData.amount < minAmount || contractData.receiverAddress === ''"
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
              height="700px"
              v-if="currentStep > 1"
            >
            <v-card-text>
              <transaction-contract
                :step="1"
                :amount="decimalAmount"
                :payerAddress="contractData.payerAddress"
                :receiverAddress="contractData.receiverAddress"
                :message="contractData.message"
                :signatures="[...contractData.signatures]"
                :slatepack="contractData.slatepackMsg"
                @withdrawal-complete="completeTx"
              ></transaction-contract>
            </v-card-text>
            </v-card>
            <v-btn small tile text class="mx-5" @click="$emit('close')">
              {{ complete ? 'Close' : 'Cancel' }}
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
import { Decimal } from 'decimal.js';

const { mapState } = createNamespacedHelpers('auth')

export default {
  name: 'WithdrawalModal',
  components: {
    'transaction-contract': TransactionContract,
  },
  props: {
    dialog: Boolean,
  },
  data: () => ({
    contractData: {
      // amount is not a number, it's a result of calling .match on a number
      amount: null,
      receiverAddress: '',
      payerAddress: String(process.env.VUE_APP_EXCHANGE_WALLET_ADDRESS),
      signatures: [],
      message: 'withdrawal grin user: arnold',
      slatepackMsg: null,
    },
    currentStep: 1,
    minAmount: new Decimal(0.1),
    complete: false,
    loading: {
      step2: false,
    },
  }),
  created: function() {
    this.contractData.message = 'withdrawal grin user: ' + this.user().username;
  },
  computed: {
    decimalAmount() {
      return new Decimal(this.contractData.amount[0]);
    }
  },
  methods: {
    restrictDecimal () {
      this.contractData.amount = this.contractData.amount.match(/^\d+\.?\d{0,9}/);
    },
    moveToStep2 () {
      this.loading.step2 = true;
      WalletService.startWithdrawal(
        'GRIN',
        this.contractData.receiverAddress,
        new Decimal(this.contractData.amount[0]),
        this.contractData.message
      )
      .then((slatepackMsg) => {
        this.contractData.slatepackMsg = slatepackMsg;
        this.currentStep = 2;
      })
      .catch((error) => {
        let msg = error.response.data.detail || 'Error occured';
        this.$toasted.error(msg);
      })
      .finally(() => {
        this.loading.step2 = false;
      });
    },
    completeTx () {
      this.complete=true;
      this.contractData.signatures.push(this.contractData.receiverAddress);
      this.contractData.signatures.push(this.contractData.payerAddress);
      this.$emit('withdrawal-complete');
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
