<template>
  <div>
    <h2 class="my-5 text-center">
      Transaction contract summary
    </h2>
    <v-row>
      <v-col class="pr-0" style="max-width: 80px">
        <strong>Type:</strong>
      </v-col>
      <v-col>
        <span style="text-transform: capitalize;">{{ txType }}</span>
      </v-col>
    </v-row>
    <v-row>
      <v-col class="pr-0" style="max-width: 80px">
        <strong>Payer:</strong>
      </v-col>
      <v-col>
        {{ payer }}
      </v-col>
    </v-row>
    <v-row>
      <v-col class="pr-0" style="max-width: 80px">
        <strong>Receiver:</strong>
      </v-col>
      <v-col>
        {{ receiver }}
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
          rows="4"
          class="pt-0 mt-0"
          disabled
        ></v-textarea>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <strong>Signatures ({{ signatures.length + '/' + nrParticipants }}):</strong>
        <ul v-if="signatures.length > 0">
          <li v-for="signature in signatures" :key="signature">
            {{ signature }}
            <v-icon class="pb-2" color="primary" aria-hidden="false">
              mdi-check
            </v-icon>
          </li>
        </ul>
        <span v-else class="ml-5">Nobody has signed the contract yet</span>
      </v-col>
    </v-row>
    <v-col class="text-right">
      <v-btn
        v-if="needsSignature"
        color="primary"
        class="black--text"
        @click="signContract"
        :loading="loading.signing"
      >
        Sign contract
      </v-btn>
      <v-btn
        v-else
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
import { Decimal } from 'decimal.js';

export default {
  name: 'TransactionContract',
  props: {
    nrParticipants: Number,
    txType: String,
    amount: Decimal,
    ownerAddress: String,
    thirdPartyAddress: String,
    ownerInitiated: Boolean,
    message: String,
    signatures: Array,
    slatepackMsgToCopy: {
      type: String,
      default: '',
    },
  },
  computed: {
    payer: function () {
      if (this.txType === 'invoice') {
        return this.ownerInitiated ? this.thirdPartyAddress : this.ownerAddress;
      } else {
        // payment type
        return this.ownerInitiated ? this.ownerAddress : this.thirdPartyAddress;
      }
    },
    receiver: function () {
      return this.payer === this.ownerAddress ? this.thirdPartyAddress : this.ownerAddress;
    },
    needsSignature: function() {
      if (this.signatures.includes(this.ownerAddress)) {
        return false;
      }
      return this.ownerInitiated ? this.signatures.length > 0 : true;
    },
  },
  data: () => ({
    loading: {
      signing: false,
    },
  }),
  methods: {
    copySlatepackMsg: function() {
      copyToClipboard(this.slatepackMsgToCopy);
      this.$toasted.show('Transaction contract copied!')
    },
    signContract: function() {
      this.loading.signing = true;
      setTimeout(() => {
        this.loading.signing = false;
        this.$emit('signed');
      }, 2000);
    },
  },
}
</script>
