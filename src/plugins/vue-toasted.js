import Vue from 'vue';
import Toasted from 'vue-toasted';

Vue.use(Toasted, {
  iconPack: 'mdi',
  duration: 8000,
  className: 'title',
  keepOnHover: true,
});
