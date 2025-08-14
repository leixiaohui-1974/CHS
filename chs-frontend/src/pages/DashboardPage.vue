<template>
  <div class="dashboard-container">
    <a-page-header title="Project Dashboard" />
    <div class="project-list-container">
      <a-button type="primary" @click="showCreateModal" style="margin-bottom: 16px;">
        Create Project
      </a-button>
      <a-list bordered :data-source="projects">
        <template #renderItem="{ item }">
          <a-list-item>
            <a-list-item-meta :description="item.description">
              <template #title>
                <router-link :to="{ name: 'ProjectDetail', params: { id: item.id } }">{{ item.name }}</router-link>
              </template>
            </a-list-item-meta>
          </a-list-item>
        </template>
      </a-list>
    </div>

    <a-modal
      v-model:open="isModalVisible"
      title="Create New Project"
      @ok="handleCreateProject"
      @cancel="handleCancel"
    >
      <a-form :model="formState" ref="formRef" layout="vertical">
        <a-form-item
          label="Project Name"
          name="name"
          :rules="[{ required: true, message: 'Please input the project name!' }]"
        >
          <a-input v-model:value="formState.name" />
        </a-form-item>
        <a-form-item label="Description" name="description">
          <a-textarea v-model:value="formState.description" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { storeToRefs } from 'pinia';
import { useProjectStore } from '../store/projectStore';
import { useRouter } from 'vue-router';

const projectStore = useProjectStore();
const { projects } = storeToRefs(projectStore);
const { createProject } = projectStore;
const router = useRouter();

const isModalVisible = ref(false);
const formRef = ref();
const formState = reactive({
  name: '',
  description: '',
});

const showCreateModal = () => {
  isModalVisible.value = true;
};

const handleCreateProject = async () => {
  try {
    await formRef.value.validate();
    await createProject({ ...formState });
    isModalVisible.value = false;
    formState.name = '';
    formState.description = '';
  } catch (error) {
    console.error('Validation failed:', error);
  }
};

const handleCancel = () => {
  isModalVisible.value = false;
};
</script>

<style scoped>
.dashboard-container {
  padding: 24px;
}
.project-list-container {
  max-width: 800px;
  margin: 0 auto;
}
</style>
