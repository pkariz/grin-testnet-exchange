<template>
  <v-container style="margin-top: 20px;">
      <h3>Instructions for testnet grin exchange - Rust implementation</h3>
      <v-card class="my-4">
        <v-card-title>
          Deposit
        </v-card-title>
        <v-card-text>
          <strong>Note:</strong>
          <p>Deposit uses an invoice flow (RSR) to let the exchange finalize the transaction.</p>
          <strong>Step1:</strong>
          <p>Insert the amount and your wallet address. The amount should be in Grin and not NanoGrin (use dot for decimals). You can get your wallet address by running: <code>grin-wallet --testnet address</code>. Example of a wallet address: <code>tgrin1vsdvjhyv2rqnc8pw0g9d7atx8z32uq52r6vjk9tlh6tmkfxl8zksg7u4ut</code>. The message displayed is currently there for no particular reason as it isn't really a part of the payment proof (payment proofs are not yet implemented for the invoice flow). After you're done with this step click continue.</p>
          <strong>Step2:</strong>
          <p>Here you get the overall transaction info. Click on <code>Copy contract</code> (this copies an encrypted slatepack for your wallet) and run command <code>grin-wallet --testnet pay -m</code>. It will then ask you for slatepack and you just paste it here. You will need to confirm the amount, so just type it in (or copy it) and press enter. At the end of the output you will get longer slatepack, copy it. Then click <code>Continue</code> to move to the <code>Signature</code> step.</p>
          <strong>Step3:</strong>
          <p>Here you click in the field and paste the copied slatepack. After that, you will get a message that the transaction has been broadcasted and you will need to wait for the confirmations. Until it gets 10 confirmations this amount will be locked.</p>
        </v-card-text>
      </v-card>
      <v-card class="my-4">
        <v-card-title>
          Withdrawal
        </v-card-title>
        <v-card-text>
          <strong>Note:</strong>
          <p>Withdrawal uses a payment flow (SRS) to let the exchange finalize the transaction.</p>
          <strong>Step1:</strong>
          <p>Insert the amount and your wallet address. The amount should be in Grin and not NanoGrin (use dot for decimals). You can get your wallet address by running: <code>grin-wallet --testnet address</code>. Example of a wallet address: <code>tgrin1vsdvjhyv2rqnc8pw0g9d7atx8z32uq52r6vjk9tlh6tmkfxl8zksg7u4ut</code>. The message displayed is currently there for no particular reason as it isn't really a part of the payment proof (payment proof is created for this transaction but implementation currently doesn't include message in it). After you're done with this step click continue.</p>
          <strong>Step2:</strong>
          <p>Here you get the overall transaction info. Click on <code>Copy contract</code> (this copies an encrypted slatepack for your wallet) then run command <code>grin-wallet --testnet receive -m</code>. It will then ask you for the slatepack and you just paste it here. At the end of the output you will get a longer slatepack, copy it. Then click <code>Continue</code> to move to the <code>Signature</code> step.</p>
          <strong>Step3:</strong>
          <p>Here you click in the field and paste the copied slatepack. After that, you will get a message that the transaction has been broadcasted and you will need to wait for the confirmations. Until it gets 10 confirmations this amount will be locked.</p>
        </v-card-text>
      </v-card>
  </v-container>
</template>

<script>
  export default {
    name: 'Home',
  }
</script>
