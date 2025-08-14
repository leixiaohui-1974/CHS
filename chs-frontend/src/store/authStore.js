import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('authToken'));

  function setToken(newToken) {
    token.value = newToken;
    if (newToken) {
      localStorage.setItem('authToken', newToken);
    } else {
      localStorage.removeItem('authToken');
    }
  }

  async function login(username, password) {
    // Mock API call
    return new Promise(resolve => {
      setTimeout(() => {
        const fakeToken = 'fake-token-' + Date.now();
        setToken(fakeToken);
        resolve(true);
      }, 1000);
    });
  }

  function logout() {
    setToken(null);
    // The component is now responsible for redirection.
  }

  return { token, login, logout };
});
