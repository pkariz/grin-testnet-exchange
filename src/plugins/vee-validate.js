import Vue from 'vue';
import { ValidationProvider, ValidationObserver } from 'vee-validate';
import { extend } from 'vee-validate';
import { required, min, min_value } from 'vee-validate/dist/rules';

extend('min_value', {
  ...min_value,
  message: 'Minimum value for {_field_} is {min}.',
})
extend('required', {
  ...required,
  message: '{_field_} is required.',
})
extend('min', {
  ...min,
  message: '{_field_} may not be smaller than {length} characters.',
})

extend('password', {
  params: ['target'],
  validate(value, { target }) {
    return value === target;
  },
  message: 'Password confirmation does not match'
});

// Register it globally
Vue.component('ValidationProvider', ValidationProvider);
Vue.component('ValidationObserver', ValidationObserver);
