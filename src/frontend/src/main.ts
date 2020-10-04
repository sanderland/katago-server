// frontend/src/main.ts

import Vue from 'vue'
import App from './App.vue'

import Buefy from 'buefy'
import 'buefy/dist/buefy.css'

Vue.use(Buefy);

const vue = new Vue({
  render: h => h(App)
});

vue.$mount('#app');
