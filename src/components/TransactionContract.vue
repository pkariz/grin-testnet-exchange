<template>
  <div>
    <h2 class="my-5 text-center">
      Transaction contract summary
    </h2>
    <v-row>
      <v-col class="pr-0" style="max-width: 80px">
        <strong>Payer:</strong>
      </v-col>
      <v-col>
        {{ payerAddress }}
      </v-col>
    </v-row>
    <v-row>
      <v-col class="pr-0" style="max-width: 80px">
        <strong>Receiver:</strong>
      </v-col>
      <v-col>
        {{ receiverAddress }}
      </v-col>
    </v-row>
    <v-row>
      <v-col class="pr-0" style="max-width: 80px">
        <strong>Amount:</strong>
      </v-col>
      <v-col>
        {{ amount }} Grin
      </v-col>
    </v-row>
    <v-row>
      <v-col class="pr-0" style="max-width: 80px">
        <strong>Message:</strong>
      </v-col>
      <v-col>
        <v-textarea
          v-model="message"
          name="message"
          rows="2"
          class="pt-0 mt-0"
          disabled
        ></v-textarea>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <strong>Signatures ({{ signatures.length + '/2' }}):</strong>
        <ul v-if="signatures.length > 0">
          <li v-for="signature in signatures" :key="signature">
            {{ signature }}
            <v-icon class="pb-2" color="primary" aria-hidden="false">
              mdi-check
            </v-icon>
          </li>
        </ul>
        <span v-else class="ml-5">Nobody has signed the contract yet</span>
        <br>
        <h2 class="mt-5" v-if="step === 2 && signed">
          Please copy the contract, sign it with your wallet and broadcast the transaction. Once the transaction lands on the chain
          and gets enough confirmations your grin balance on the exchange will be automatically credited.
        </h2>
        <h2 class="mt-5" v-if="step === 1">
          Please copy the contract, sign it with your wallet and paste signed contract on the next step.
        </h2>
        <br>
      </v-col>
    </v-row>
    <v-col class="text-right">
      <v-btn
        v-if="step !== 1 && !signed"
        color="primary"
        class="black--text"
        @click="signContract"
        :loading="loading.signing"
      >
        Sign contract
      </v-btn>
      <v-btn
        v-if="step === 1 || signed"
        color="primary"
        class="black--text"
        @click="copySlatepackMsg"
      >
        Copy contract
      </v-btn>
    </v-col>
  </div>
</template>

<script>
import { copyToClipboard } from '@/shared/helpers';
import WalletService from '@/services/wallet';
import { Decimal } from 'decimal.js';

export default {
  name: 'TransactionContract',
  props: {
    amount: Decimal,
    // payerAddress is user's address
    payerAddress: String,
    // receiverAddress is exchange's address
    receiverAddress: String,
    step: Number,
    message: String,
    signatures: Array,
    slatepack: String,
  },
  data: () => ({
    loading: {
      signing: false,
    },
    signed: false,
    signedSlatepackMsg: null,
  }),
  methods: {
    copySlatepackMsg: function() {
      let copySlatepackMsg = this.slatepack;
      if (this.step !== 1) {
        copySlatepackMsg = this.signedSlatepackMsg;
      }
      if (!copySlatepackMsg) {
        this.$toasted.error('Invalid slatepack msg');
        return;
      }
      copyToClipboard(copySlatepackMsg);
      this.$toasted.show('Transaction contract copied!')
    },
    signContract: function() {
      this.loading.signing = true;
      WalletService.finishDeposit(
        'GRIN',
        this.slatepack,
      ).then((data) => {
        this.signedSlatepackMsg = data.slatepack;
        this.signatures.push(this.receiverAddress);
        this.signed = true;
        this.$emit('signed');
      }).catch((error) => {
        this.$toasted.error(error.response.data.detail);
      }).finally(() => {
        this.loading.signing = false;
      });
    },
  },
}
</script>
