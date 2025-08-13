<template>
  <div class="login-container">
    <a-card title="Login" :style="{ width: '400px' }">
      <a-form
        :model="formState"
        name="login"
        layout="vertical"
        @finish="onFinish"
        @finishFailed="onFinishFailed"
      >
        <a-form-item
          label="Email or Username"
          name="email"
          :rules="[{ required: true, message: 'Please input your email or username!' }]"
        >
          <a-input v-model:value="formState.email" />
        </a-form-item>

        <a-form-item
          label="Password"
          name="password"
          :rules="[{ required: true, message: 'Please input your password!' }]"
        >
          <a-input-password v-model:value="formState.password" />
        </a-form-item>

        <a-form-item>
          <a-button type="primary" html-type="submit" block>Log in</a-button>
        </a-form-item>

        <div style="text-align: center;">
          Don't have an account? <router-link to="/register">Register now!</router-link>
        </div>
      </a-form>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue';
import { RouterLink } from 'vue-router';
import { useAuthStore } from '@/stores/authStore';
import { Card as ACard, Form as AForm, FormItem as AFormItem, Input as AInput, InputPassword as AInputPassword, Button as AButton, message } from 'ant-design-vue';

const authStore = useAuthStore();
const formState = reactive({
  email: '',
  password: '',
});
const isLoading = ref(false);

const onFinish = async (values: any) => {
  isLoading.value = true;
  try {
    // The backend endpoint is /api/auth/signin and expects a LoginRequest payload
    // which has { usernameOrEmail, password }. We'll use the email from the form.
    await authStore.login({
      usernameOrEmail: values.email,
      password: values.password
    });
    message.success('Login successful!');
  } catch (error) {
    message.error('Login failed. Please check your credentials.');
  } finally {
    isLoading.value = false;
  }
};

const onFinishFailed = (errorInfo: any) => {
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
