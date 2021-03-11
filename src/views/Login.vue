<template>
  <v-container dark style="margin-top: 20px;">
  <v-card class="mx-auto" max-width="600px">
    <v-toolbar>
      <v-spacer></v-spacer>
      <v-toolbar-title>Login</v-toolbar-title>
      <v-spacer></v-spacer>
    </v-toolbar>
    <v-card-text>
      <v-container>
        <ValidationObserver
          v-slot="{ invalid, validated, handleSubmit }"
        >
          <v-form @submit.prevent="handleSubmit(onSubmit)">
            <v-row>
              <v-col cols="12">
                <ValidationProvider
                  name="username"
                  rules="required"
                  v-slot="{ errors }"
                >
                  <v-text-field
                    v-model="username"
                    :error-messages="errors"
                    prepend-icon="mdi-account"
                    label="Username"
                  ></v-text-field>
                </ValidationProvider>
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="12">
                <ValidationProvider
                  name="password"
                  rules="required"
                  v-slot="{ errors }"
                >
                  <v-text-field
                    type="password"
                    v-model="password"
                    :error-messages="errors"
                    prepend-icon="mdi-lock"
                    name="password"
                    label="Password"
                  ></v-text-field>
                </ValidationProvider>
              </v-col>
            </v-row>
            <br />
            <v-row justify="center" align="center">
              <v-spacer></v-spacer>
              <v-col>
                <v-btn
                  type="submit"
                  color="primary"
                  class="black--text"
                  block
                  :disabled="invalid || !validated"
                  >Login</v-btn
                >
              </v-col>
              <v-spacer></v-spacer>
            </v-row>
          </v-form>
        </ValidationObserver>
      </v-container>
    </v-card-text>
  </v-card>
  </v-container>
</template>

<script>
import { createNamespacedHelpers } from 'vuex'

const { mapActions } = createNamespacedHelpers('auth')

export default {
  name: 'Login',
  data: () => ({
    username: '',
    password: '',
  }),
  methods: {
    onSubmit: function() {
      this.login({ username: this.username, password: this.password })
        .then(() => {
          this.$toasted.show('Welcome');
          this.$router.push({ name: 'balance' });
        })
        .catch(() => {
          this.$toasted.error('Invalid data');
        });
    },
    ...mapActions([
      'login',
    ]),
  },
}
</script>
