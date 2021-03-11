<template>
  <v-app>
    <v-app-bar
      app
    >
      <div class="d-flex align-center" @click="routeTo('home')">
        <v-img
          alt="Grin Logo"
          class="shrink mr-2"
          contain
          src="https://aws1.discourse-cdn.com/standard10/uploads/grin/original/1X/f96e1cdce64456785297c317e6cb84f3fab2edcb.svg"
          transition="scale-transition"
          width="40"
        />
        <v-btn text class="no-active">
          Instructions
        </v-btn>
      </div>

      <v-spacer></v-spacer>

      <template v-if="$vuetify.breakpoint.smAndUp">
        <v-btn small tile color="primary" class="black--text mx-2" v-for="(item, i) in menuItems" :key="i" @click="item.clickHandler">
          <v-icon>{{ item.icon }}</v-icon>&nbsp;{{ item.text }}
        </v-btn>
      </template>
      <template v-else>
        <v-menu bottom left>
          <template v-slot:activator="{ on, attrs }">
            <v-btn icon v-bind="attrs" v-on="on">
              <v-icon>mdi-dots-vertical</v-icon>
            </v-btn>
          </template>
          <v-list>
            <v-list-item
              v-for="(item, i) in menuItems"
              :key="i"
              @click="item.clickHandler"
            >
              <v-list-item-icon>
                <v-icon>{{ item.icon }}</v-icon>
              </v-list-item-icon>
              <v-list-item-title>
                {{ item.text }}
              </v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </template>
    </v-app-bar>

    <v-main>
      <router-view/>
    </v-main>
  </v-app>
</template>

<script>
import { createNamespacedHelpers } from 'vuex'

const { mapGetters, mapActions } = createNamespacedHelpers('auth')

export default {
  name: 'App',

  data: () => ({
  }),
  computed: {
    menuItems() {
      if(!this.isLoggedIn()) {
        return [
          { text: 'Login', icon: 'mdi-login', clickHandler: () => this.routeTo('login') },
          { text: 'Register', icon: 'mdi-account-plus', clickHandler: () => this.routeTo('register') },
        ];
      }
      return [
        { text: 'Balance', icon: 'mdi-cash', clickHandler: () => this.routeTo('balance') },
        { text: 'Logout', icon: 'mdi-logout', clickHandler: () => this.performLogout() },
      ];
    }
  },
  methods: {
    performLogout: function() {
      this.logout()
        .then(() => {
          this.$toasted.show('Bye bye');
          this.routeTo('home');
        })
    },
    routeTo: function(routeName) {
      if (this.$router.currentRoute.name !== routeName) {
        this.$router.push({ name: routeName });
      }
    },
    ...mapGetters([
      'isLoggedIn',
    ]),
    ...mapActions([
      'logout',
    ]),
  },
};
</script>
<style>
.v-btn--active.no-active::before {
  opacity: 0 !important;
}
</style>
