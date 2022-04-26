<template>
  <v-container style="margin-top: 20px;">
      <h3>Instructions for testnet grin exchange - Rust implementation</h3>
      <v-card class="my-4">
        <v-card-title>
          Deposit
        </v-card-title>
        <v-card-text>
          <strong>Step1:</strong>
          <p>Create a new contract where you send some amount to the exchange (the following example will deposit 1.2 grin). You can do this by running grin-wallet cli cmd: <code>./grin-wallet --testnet contract new --send=1.2 --encrypt-for=tgrin1vsdvjhyv2rqnc8pw0g9d7atx8z32uq52r6vjk9tlh6tmkfxl8zksg7u4ut</code>. Paste the resulting slatepack in the textarea.</p>
          <strong>Step2:</strong>
          <p>Here you get the overall contract info which is already signed by the exchange. Click on <code>Copy contract</code> (this copies an encrypted slatepack for your wallet), then run command <code>./grin-wallet --testnet contract sign --send=1.2</code> and paste copied slatepack when asked. This command will sign the contract and broadcast it. Now you need to wait for tx to get 3 confirmations, until then the deposited amount will be locked.</p>
        </v-card-text>
      </v-card>
      <v-card class="my-4">
        <v-card-title>
          Withdrawal
        </v-card-title>
        <v-card-text>
          <strong>Step1:</strong>
          <p>Insert the amount and your wallet address. The amount should be in Grin and not NanoGrin (use dot for decimals). You can get your wallet address by running: <code>./grin-wallet --testnet address</code>. Example of a wallet address: <code>tgrin1vsdvjhyv2rqnc8pw0g9d7atx8z32uq52r6vjk9tlh6tmkfxl8zksg7u4ut</code>. After you're done with this step click continue.</p>
          <strong>Step2:</strong>
          <p>Here you get the overall transaction info. Click on <code>Copy contract</code> (this copies an encrypted slatepack for your wallet) then run command <code>./grin-wallet --testnet contract sign --receive=30 --no-payjoin</code>. If you want to payjoin as a receiver remove the <code>--no-payjoin</code> flag. After you execute the contract sign command, you will need to paste the slatepack. At the end of the output you will get a longer slatepack, copy it. Then click in the field below and paste the copied slatepack. After that, you will get a message that the transaction has been broadcasted and you will need to wait for the confirmations. Until it gets 3 confirmations this amount will be locked.</p>
        </v-card-text>
      </v-card>
  </v-container>
</template>

<script>
  export default {
    name: 'Home',
  }
</script>
