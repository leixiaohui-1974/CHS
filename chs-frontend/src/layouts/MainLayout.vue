<template>
  <a-layout style="min-height: 100vh">
    <a-layout-sider v-model:collapsed="collapsed" collapsible>
      <div class="logo" />
      <a-menu v-model:selectedKeys="selectedKeys" theme="dark" mode="inline">
        <a-menu-item key="1">
          <router-link to="/">
            <pie-chart-outlined />
            <span>Projects</span>
          </router-link>
        </a-menu-item>
        <a-menu-item key="2">
          <router-link to="/devices">
            <desktop-outlined />
            <span>Edge Devices</span>
          </router-link>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>
    <a-layout>
      <a-layout-content style="margin: 16px">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>
<script setup>
import { ref } from 'vue';
import {
  PieChartOutlined,
  DesktopOutlined,
} from '@ant-design/icons-vue';
const collapsed = ref(false);
const selectedKeys = ref(['1']);
</script>
<style scoped>
.logo {
  height: 32px;
  background: rgba(255, 255, 255, 0.3);
  margin: 16px;
}
</style>
