<template>
  <div class="login-container">
    <a-card title="Login" :style="{ width: '350px' }">
      <a-form
        :model="formState"
        name="basic"
        autocomplete="off"
        @finish="onFinish"
        @finishFailed="onFinishFailed"
      >
        <a-form-item
          label="Username"
          name="username"
          :rules="[{ required: true, message: 'Please input your username!' }]"
        >
          <a-input v-model:value="formState.username" />
        </a-form-item>

        <a-form-item
          label="Password"
          name="password"
          :rules="[{ required: true, message: 'Please input your password!' }]"
        >
          <a-input-password v-model:value="formState.password" />
        </a-form-item>

        <a-form-item>
          <a-button type="primary" html-type="submit" :loading="loading">Login</a-button>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../store/authStore';

const router = useRouter();
const authStore = useAuthStore();
const formState = reactive({
  username: '',
  password: '',
});
const loading = ref(false);

const onFinish = async (values) => {
  loading.value = true;
  try {
    const success = await authStore.login(values.username, values.password);
    if (success) {
      router.push('/');
    }
  } catch (error) {
    console.error('Login failed:', error);
  } finally {
    loading.value = false;
  }
};

const onFinishFailed = errorInfo => {
  console.log('Failed:', errorInfo);
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f0f2f5;
}
</style>
