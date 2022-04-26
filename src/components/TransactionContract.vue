<template>
  <div>
    <h2 class="my-5 text-center" v-if="!loading.initial">
      Transaction contract summary
    </h2>
    <v-row class="text-center align-self-center justify-center" style="height: 600px" v-if="loading.initial">
      <v-col cols="12" class="my-5" style="height: 50px">
        <h2>Signing contract</h2>
      </v-col>
      <v-col style="height: 100%">
      <v-progress-circular
        indeterminate
        color="primary"
        class="pt-0 text-center justify-center"
      ></v-progress-circular>
      </v-col>
    </v-row>
    <template v-else>
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
        v-if="(step === 1 || signed) && !validPastedSlatepackMsg"
        color="primary"
        class="black--text mb-8"
        @click="copySlatepackMsg"
      >
        Copy contract
      </v-btn>
    </v-col>
    <v-row v-if="step === 1">
      <v-col>
        <v-divider></v-divider>
        <v-row class="text-center align-self-center justify-center" style="height: 600px" v-if="loading.verifyingSlatepack">
          <v-col cols="12" class="my-5 pt-5" style="height: 50px">
            <h2>Signing transaction contract</h2>
          </v-col>
          <v-col style="height: 100%">
          <v-progress-circular
            indeterminate
            color="primary"
            class="pt-0 text-center justify-center"
          ></v-progress-circular>
          </v-col>
        </v-row>
        <template v-else-if="!pastedSlatepackMsg || !validPastedSlatepackMsg">
          <h3 class="mt-5">
            Please copy the contract and sign it with your wallet using the command:<br>
            ./grin-wallet --testnet contract sign --receive={{ amount }} --no-payjoin&nbsp;&nbsp;
          <v-fab-transition>
            <v-icon v-if="cmdCopied" color="yellow">mdi-check</v-icon>
            <v-icon v-else @click.stop="copyCmd(`./grin-wallet --testnet contract sign --receive=${amount} --no-payjoin`)">
              mdi-content-copy
            </v-icon>
          </v-fab-transition>
            <br><br>
            Please paste the resulting new contract in the input area below.
          </h3>
          <v-textarea
            id="pastedSlatepackMsg"
            v-model="pastedSlatepackMsg"
            name="pasted-slatepack-msg"
            label="Paste signed contract"
            class="pa-0 mt-5"
            rows="2"
            @input="onSlatepackPaste"
            :loading="loading.verifyingSlatepack"
          ></v-textarea>
        </template>
        <v-row class="text-center align-self-center justify-center" style="height: 100px" v-else>
          <v-col cols="12" class="mt-5 pt-5" style="height: 110px">
            <h2>Transaction contract completed</h2>
            <br>
            <v-icon large color="primary">
              mdi-check
            </v-icon>
          </v-col>
          <v-col cols="12">
            <h3>Please check your withdrawal history for on-chain confirmation. We have locked the withdrawal amount,
            once the transaction lands on the chain and gets enough confirmations your grin balance on the exchange
            will be automatically reduced.</h3>
          </v-col>
        </v-row>
      </v-col>
    </v-row>
    <v-row class="mt-5" v-else-if="step === 2 && signed">
      <v-col>
        <v-divider></v-divider>
        <h3 class="mt-5">
          Please copy the contract and sign it with your wallet using the command:<br>
          ./grin-wallet --testnet contract sign&nbsp;&nbsp;
          <v-fab-transition>
            <v-icon v-if="cmdCopied" color="yellow">mdi-check</v-icon>
            <v-icon v-else @click.stop="copyCmd(`./grin-wallet --testnet contract sign`)">
              mdi-content-copy
            </v-icon>
          </v-fab-transition>
          <br><br>
          Once the transaction lands on the chain and gets enough confirmations your grin balance on the exchange will be automatically credited.
        </h3>
      </v-col>
    </v-row>
    </template>
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
    autoSign: Boolean,
  },
  data: () => ({
    loading: {
      initial: false,
      signing: false,
      verifyingSlatepack: false,
    },
    signed: false,
    signedSlatepackMsg: null,
    pastedSlatepackMsg: null,
    validPastedSlatepackMsg: false,
    cmdCopied: false,
  }),
  created: function() {
    if (this.autoSign) {
      this.signContract();
    }
  },
  methods: {
    onSlatepackPaste () {
      if (this.pastedSlatepackMsg === '') {
        return;
      }
      this.loading.verifyingSlatepack = true;
      WalletService.finishWithdrawal(
        'GRIN',
        { 'slatepack_msg': this.pastedSlatepackMsg }
      ).then(() => {
        setTimeout(() => {
          this.validPastedSlatepackMsg = true;
          this.loading.verifyingSlatepack = false;
          this.$emit('withdrawal-complete');
        }, 1000);
      }).catch(() => {
        setTimeout(() => {
          this.$toasted.error('Transaction contract signing failed');
          this.loading.verifyingSlatepack = false;
        }, 1000);
      });
    },
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
      this.$emit('copied');
    },
    signContract: function() {
      if (this.autoSign) {
        this.loading.initial = true;
      }
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
        if (this.autoSign) {
          setTimeout(() => {
            this.loading.initial = false;
          }, 1000);
        }
      });
    },
    copyCmd: function(cmd) {
      copyToClipboard(cmd);
      this.cmdCopied = true;
      setTimeout(() => {
        this.cmdCopied = false;
      }, 2000);
    },
  },
}
</script>
