<template>
  <a-layout style="height: 100vh;">
    <a-layout-sider width="300" theme="light" collapsible>
      <SceneManager />
    </a-layout-sider>
    <a-layout>
      <a-layout-header style="background: #fff; padding: 0 16px;">
        <h2>Modeling Canvas - Project {{ projectId }}</h2>
      </a-layout-header>
      <a-layout-content style="margin: 16px;">
        <div class="map-wrapper">
          <GisMap />
        </div>
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import GisMap from '@/components/GisMap.vue';
import SceneManager from '@/components/SceneManager.vue';

const route = useRoute();
const projectId = ref<string | string[] | null>(null);

onMounted(() => {
  projectId.value = route.params.id;
});
</script>

<style scoped>
.map-wrapper {
  height: 100%;
  width: 100%;
  background: #f0f2f5;
}
</style>
