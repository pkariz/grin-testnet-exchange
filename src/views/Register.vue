<template>
  <v-container dark style="margin-top: 20px;">
  <v-card class="mx-auto" max-width="600px">
    <v-toolbar>
      <v-spacer></v-spacer>
      <v-toolbar-title>Register</v-toolbar-title>
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
                  rules="required|min:5"
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
            <br>
            <ValidationObserver>
              <v-row>
                <v-col cols="12">
                  <ValidationProvider
                    name="password"
                    rules="required|min:8|password:@confirmPassword"
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
                <v-col cols="12">
                  <ValidationProvider
                    name="confirmPassword"
                    rules="required"
                    v-slot="{ errors }"
                  >
                    <v-text-field
                      type="password"
                      v-model="confirmPassword"
                      :error-messages="errors"
                      prepend-icon="mdi-lock"
                      name="confirmPassword"
                      label="Confirm password"
                    ></v-text-field>
                  </ValidationProvider>
                </v-col>
              </v-row>
            </ValidationObserver>
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
                  >Register</v-btn
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
  name: 'Register',
  data: () => ({
    username: '',
    password: '',
    confirmPassword: '',
  }),
  methods: {
    onSubmit: function() {
      this.register({ username: this.username, password: this.password })
        .then(() => {
          this.$toasted.show('Registered, you can login now');
          this.$router.push({ name: 'login' });
        })
        .catch((error) => {
          let messages = [];
          if (error.response.data) {
            for (const attr in error.response.data) {
              if (Array.isArray(error.response.data[attr])) {
                messages.push(`${attr}: ` + error.response.data[attr].join(', '));
              } else {
                messages.push(error.response.data[attr]);
              }
            }
            this.$toasted.error(messages.join('<br>'));
          } else {
            this.$toasted.error('Registration failed');
          }
        });
    },
    ...mapActions([
      'register',
    ]),
  },
}
</script>
