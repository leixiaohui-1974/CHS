<template>
  <div class="dashboard-container">
    <h1>Project Dashboard</h1>
    <a-button type="primary" @click="showAddModal" style="margin-bottom: 16px;">
      Create Project
    </a-button>

    <a-table :columns="columns" :data-source="projectStore.projects" :loading="projectStore.isLoading" row-key="id">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'action'">
          <a-space>
            <a-button type="link" @click="showEditModal(record)">Edit</a-button>
            <a-popconfirm
              title="Are you sure you want to delete this project?"
              @confirm="handleDelete(record.id)"
            >
              <a-button type="link" danger>Delete</a-button>
            </a-popconfirm>
            <a-button type="link" @click="openWorkbench(record.id)">Open Workbench</a-button>
          </a-space>
        </template>
      </template>
    </a-table>

    <a-modal
      v-model:open="isModalVisible"
      :title="isEditing ? 'Edit Project' : 'Create Project'"
      @ok="handleOk"
      :confirm-loading="isConfirmLoading"
    >
      <a-form ref="formRef" :model="formState" layout="vertical">
        <a-form-item
          label="Project Name"
          name="name"
          :rules="[{ required: true, message: 'Please enter a project name' }]"
        >
          <a-input v-model:value="formState.name" />
        </a-form-item>
        <a-form-item
          label="Description"
          name="description"
          :rules="[{ required: true, message: 'Please enter a description' }]"
        >
          <a-textarea v-model:value="formState.description" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useProjectStore } from '@/stores/projectStore';
import type { Project } from '@/services/projectService';

const router = useRouter();
const projectStore = useProjectStore();

const columns = [
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Description', dataIndex: 'description', key: 'description' },
  { title: 'Actions', key: 'action' },
];

const isModalVisible = ref(false);
const isEditing = ref(false);
const isConfirmLoading = ref(false);
const editingProjectId = ref<number | null>(null);

const formRef = ref();
const formState = reactive({
  name: '',
  description: '',
});

onMounted(() => {
  projectStore.fetchProjects();
});

const showAddModal = () => {
  isEditing.value = false;
  formState.name = '';
  formState.description = '';
  isModalVisible.value = true;
};

const showEditModal = (project: Project) => {
  isEditing.value = true;
  editingProjectId.value = project.id;
  formState.name = project.name;
  formState.description = project.description;
  isModalVisible.value = true;
};

const handleOk = async () => {
  try {
    await formRef.value.validate();
    isConfirmLoading.value = true;
    if (isEditing.value && editingProjectId.value !== null) {
      await projectStore.editProject(editingProjectId.value, formState);
    } else {
      await projectStore.addProject(formState);
    }
    isModalVisible.value = false;
  } catch (error) {
    // Validation failed
  } finally {
    isConfirmLoading.value = false;
  }
};

const handleDelete = (id: number) => {
  projectStore.removeProject(id);
};

const openWorkbench = (id: number) => {
  router.push({ name: 'workbench', params: { id } });
};
</script>

<style scoped>
.dashboard-container {
  padding: 24px;
}
</style>
