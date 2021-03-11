import axios from 'axios';
import Router from '@/router';
import Vue from 'vue';
import store from '@/store/index';

const BACKEND_URL = String(process.env.VUE_APP_BACKEND_URL);
const ACCESS_TOKEN = 'access_token';
const REFRESH_TOKEN = 'refresh_token';
const API_TIMEOUT = 5000;

//
const defaultApi = axios.create({
  baseURL: BACKEND_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    accept: 'application/json',
  },
});

// this is axios instance with jwt header
const api = axios.create({
  baseURL: BACKEND_URL,
  timeout: API_TIMEOUT,
  headers: {
    Authorization: `Bearer ${window.localStorage.getItem(ACCESS_TOKEN)}`,
    'Content-Type': 'application/json',
  },
});

const registerUser = (username, password) => {
  return defaultApi.post('/api/account/register/', { username, password });
};

const loginUser = (username, password) => {
  return defaultApi.post('/api/account/token/', { username, password })
    .then((response) => {
      window.localStorage.setItem(ACCESS_TOKEN, response.data.access);
      window.localStorage.setItem(REFRESH_TOKEN, response.data.refresh);
      api.defaults.headers.Authorization = `Bearer ${response.data.access}`;
      return response.data;
    }).catch((error) => {
      throw error;
    });
};

const refreshToken = () => {
  const refresh = window.localStorage.getItem(REFRESH_TOKEN);
  return defaultApi.post('/api/account/token/access/', { refresh })
    .then((response) => {
      window.localStorage.setItem(ACCESS_TOKEN, response.data.access);
      return response.data;
    });
};

const logoutUser = () => {
  // remove both tokens and remove jwt header
  window.localStorage.removeItem(ACCESS_TOKEN);
  window.localStorage.removeItem(REFRESH_TOKEN);
  api.defaults.headers.Authorization = '';
};

const errorInterceptor = (error) => {
  const oldAxios = error.config;
  if (error.response === undefined) {
    throw new Error("Connection to the server failed");
  }
  if (error.response.status === 401) {
    return refreshToken().then(() => {
      // set token in headers for future api requests
      const accessToken = window.localStorage.getItem(ACCESS_TOKEN);
      const jwtHeader = `Bearer ${accessToken}`;
      api.defaults.headers.Authorization = jwtHeader;
      oldAxios.headers.Authorization = jwtHeader;
      return api(oldAxios);
    }).catch((error) => {
      // something is wrong, logout
      store.dispatch('auth/logout');
      throw error;
    });
  } else if (
    error.response.status === 403 &&
    error.response.data.code &&
    error.response.data.code === "token_not_valid"
  ) {
    store.dispatch('auth/logout');
    Vue.toasted.error('Session expired, please login again');
    Router.push({ name: 'login' });
  }
  throw error;
};

api.interceptors.response.use(
  (response) => response, // default
  (error) => errorInterceptor(error),
);

export {
  BACKEND_URL,
  ACCESS_TOKEN,
  REFRESH_TOKEN,
  API_TIMEOUT,
  defaultApi,
  api,
  registerUser,
  loginUser,
  logoutUser,
  refreshToken,
  errorInterceptor, 
};
