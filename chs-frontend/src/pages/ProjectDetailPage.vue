<template>
  <div class="project-detail-container">
    <a-page-header :title="`Project ${projectId}`" @back="() => router.push('/')" />
    <div class="scene-list-container">
      <h2>Scenes</h2>
      <a-button type="primary" @click="showCreateModal" style="margin-bottom: 16px;">
        Create Scene
      </a-button>
      <a-list bordered :data-source="scenes">
        <template #renderItem="{ item }">
          <a-list-item>
            <a-list-item-meta :description="`Mode: ${item.mode}`">
              <template #title>
                <router-link :to="{ name: 'Workbench', params: { id: projectId, sceneId: item.id } }">
                  {{ item.name }}
                </router-link>
              </template>
            </a-list-item-meta>
          </a-list-item>
        </template>
      </a-list>
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

const projectId = computed(() => route.params.id);
const scenes = computed(() => sceneStore.getScenesByProjectId(projectId.value));

const isModalVisible = ref(false);
const formRef = ref();
const formState = reactive({
  name: '',
  mode: 'SIL',
});

const showCreateModal = () => {
  isModalVisible.value = true;
};

const handleCreateScene = async () => {
  try {
    await formRef.value.validate();
    await createScene(projectId.value, { ...formState });
    isModalVisible.value = false;
    formState.name = '';
    formState.mode = 'SIL';
  } catch (error) {
    console.error('Validation failed:', error);
  }
};

const handleCancel = () => {
  isModalVisible.value = false;
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
