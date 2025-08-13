<template>
  <div class="scene-manager">
    <h4>Scene Manager</h4>
    <a-tree
      :tree-data="treeData"
      show-line
      default-expand-all
    >
      <template #title="{ title, key }">
        <span>{{ title }}</span>
      </template>
    </a-tree>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { TreeProps } from 'ant-design-vue';

const treeData = ref<TreeProps['treeData']>([
  {
    title: 'Physical Layer',
    key: '0-0',
    children: [
      { title: 'Reservoir 1', key: '0-0-0' },
      { title: 'Pipe 1', key: '0-0-1' },
    ],
  },
  {
    title: 'Instrumentation Layer',
    key: '0-1',
    children: [
        { title: 'Flow Sensor', key: '0-1-0' },
    ],
  },
  {
    title: 'Control Layer',
    key: '0-2',
    children: [
        { title: 'PID Controller', key: '0-2-0' },
    ],
  },
]);
</script>

<style scoped>
.scene-manager {
  padding: 16px;
  background-color: #fff;
  border-left: 1px solid #f0f0f0;
}
</style>
