import { defineStore } from 'pinia';
import { ref } from 'vue';
import { login as loginApi, register as registerApi, logout as logoutApi } from '@/services/authService';
import router from '@/router';

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || null);
  const isAuthenticated = ref(!!token.value);
  const user = ref(null); // To hold user info later

  async function login(credentials: any) {
    try {
      const data = await loginApi(credentials);
      token.value = data.accessToken;
      isAuthenticated.value = true;
      // You might want to fetch user details here and set user.value
      await router.push('/dashboard');
    } catch (error) {
      isAuthenticated.value = false;
      token.value = null;
      throw error;
    }
  }

  async function register(userData: any) {
    try {
      await registerApi(userData);
      // After successful registration, redirect to login
      await router.push('/login');
    } catch (error) {
      throw error;
    }
  }

  function logout() {
    logoutApi();
    token.value = null;
    isAuthenticated.value = false;
    user.value = null;
    router.push('/login');
  }

  return { token, isAuthenticated, user, login, register, logout };
});
