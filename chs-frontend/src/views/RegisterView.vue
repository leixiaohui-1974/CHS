<template>
  <div class="register-container">
    <a-card title="Register" :style="{ width: '400px' }">
      <a-form
        :model="formState"
        name="register"
        layout="vertical"
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
          label="Email"
          name="email"
          :rules="[{ required: true, type: 'email', message: 'Please input a valid email!' }]"
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
          <a-button type="primary" html-type="submit" block>Register</a-button>
        </a-form-item>

        <div style="text-align: center;">
          Already have an account? <router-link to="/login">Log in</router-link>
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
  name: '', // The backend RegisterRequest has 'name', 'username', 'email', 'password'
  username: '',
  email: '',
  password: '',
});
const isLoading = ref(false);

const onFinish = async (values: any) => {
  isLoading.value = true;
  try {
    // The backend endpoint is /api/auth/signup and expects a RegisterRequest payload.
    // We will use the username as the 'name' field for now.
    await authStore.register({
      name: values.username,
      username: values.username,
      email: values.email,
      password: values.password,
    });
    message.success('Registration successful! Please log in.');
  } catch (error) {
    message.error('Registration failed. Please try again.');
  } finally {
    isLoading.value = false;
  }
};

const onFinishFailed = (errorInfo: any) => {
  console.log('Failed:', errorInfo);
};
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f0f2f5;
}
</style>
