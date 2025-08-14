<template>
  <div class="project-detail-container">
    <a-page-header :title="`Project ${projectId}`" @back="() => router.push('/')" />
    <div class="scene-list-container">
      <h2>Scenes</h2>
      <a-button type="primary" @click="showCreateModal" style="margin-bottom: 16px;">
        Create Scene
      </a-button>

      <a-tree
        v-if="sceneTree.length"
        :tree-data="sceneTree"
        show-line
        default-expand-all
      >
        <template #title="{ title, key, data }">
          <router-link :to="{ name: 'Workbench', params: { id: projectId, sceneId: key } }">
            {{ title }}
          </router-link>
          <span style="font-size: 12px; color: #888; margin-left: 8px;">(Mode: {{ data.mode }})</span>
        </template>
      </a-tree>
      <a-empty v-else description="No scenes yet. Create one to get started!" />

    </div>

    <a-modal
      v-model:open="isModalVisible"
      title="Create New Scene"
      @ok="handleCreateScene"
      @cancel="handleCancel"
    >
      <a-form :model="formState" ref="formRef" layout="vertical">
        <a-form-item
          label="Scene Name"
          name="name"
          :rules="[{ required: true, message: 'Please input the scene name!' }]"
        >
          <a-input v-model:value="formState.name" />
        </a-form-item>
        <a-form-item
          label="Run Mode"
          name="mode"
          :rules="[{ required: true, message: 'Please select a run mode!' }]"
        >
          <a-radio-group v-model:value="formState.mode">
            <a-radio value="SIL">Software in the Loop (SIL)</a-radio>
            <a-radio value="HIL">Hardware in the Loop (HIL)</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item
          label="Parent Scene (optional)"
          name="parentId"
        >
          <a-select v-model:value="formState.parentId" placeholder="Select a base scene" allow-clear>
            <a-select-option v-for="scene in allScenesForProject" :key="scene.id" :value="scene.id">
              {{ scene.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useSceneStore } from '../store/sceneStore';

const route = useRoute();
const router = useRouter();
const sceneStore = useSceneStore();
const { createScene } = sceneStore;

const projectId = computed(() => parseInt(route.params.id, 10));

// Use the new getter for the tree view
const sceneTree = computed(() => sceneStore.getSceneTreeByProjectId(projectId.value));
// Use the old getter for the flat list needed in the modal's dropdown
const allScenesForProject = computed(() => sceneStore.getScenesByProjectId(projectId.value));

const isModalVisible = ref(false);
const formRef = ref();
const formState = reactive({
  name: '',
  mode: 'SIL',
  parentId: null, // Add parentId to form state
});

const showCreateModal = () => {
  isModalVisible.value = true;
};

const handleCreateScene = async () => {
  try {
    await formRef.value.validate();
    // Pass the whole formState, which now includes parentId
    createScene(projectId.value, { ...formState });
    isModalVisible.value = false;
    // Reset form
    formState.name = '';
    formState.mode = 'SIL';
    formState.parentId = null;
  } catch (error) {
    console.error('Validation failed:', error);
  }
};

const handleCancel = () => {
  isModalVisible.value = false;
  // Reset form
  formState.name = '';
  formState.mode = 'SIL';
  formState.parentId = null;
};
</script>

<style scoped>
.project-detail-container {
  padding: 24px;
}
.scene-list-container {
  max-width: 800px;
  margin: 0 auto;
}
</style>
