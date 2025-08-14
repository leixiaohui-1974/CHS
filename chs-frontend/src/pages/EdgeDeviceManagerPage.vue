<template>
  <div>
    <a-page-header title="Edge Device Manager" />
    <div class="manager-container">
      <a-button type="primary" @click="showRegisterModal" style="margin-bottom: 16px;">
        Register New Device
      </a-button>
      <a-table :columns="columns" :data-source="devices" row-key="id">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="record.status === 'Online' ? 'green' : 'volcano'">
              {{ record.status.toUpperCase() }}
            </a-tag>
          </template>
        </template>
      </a-table>
    </div>

    <a-modal
      v-model:open="isModalVisible"
      title="Register New Device"
      @ok="handleRegisterDevice"
      @cancel="() => isModalVisible = false"
    >
      <a-form :model="formState" ref="formRef" layout="vertical">
        <a-form-item label="Device Name" name="name" :rules="[{ required: true }]">
          <a-input v-model:value="formState.name" />
        </a-form-item>
        <a-form-item label="IP Address" name="ip" :rules="[{ required: true }]">
          <a-input v-model:value="formState.ip" />
        </a-form-item>
        <a-form-item label="Role" name="role" :rules="[{ required: true }]">
          <a-input v-model:value="formState.role" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { storeToRefs } from 'pinia';
import { useDeviceStore } from '../store/deviceStore';

const deviceStore = useDeviceStore();
const { devices } = storeToRefs(deviceStore);
const { registerDevice } = deviceStore;

const isModalVisible = ref(false);
const formRef = ref();
const formState = reactive({
  name: '',
  ip: '',
  role: '',
});

const columns = [
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'IP Address', dataIndex: 'ip', key: 'ip' },
  { title: 'Role', dataIndex: 'role', key: 'role' },
  { title: 'Status', dataIndex: 'status', key: 'status' },
];

const showRegisterModal = () => {
  isModalVisible.value = true;
};

const handleRegisterDevice = async () => {
  try {
    await formRef.value.validate();
    await registerDevice({ ...formState });
    isModalVisible.value = false;
    formState.name = '';
    formState.ip = '';
    formState.role = '';
  } catch (error) {
    console.error('Validation failed:', error);
  }
};
</script>

<style scoped>
.manager-container {
  padding: 24px;
  background: #fff;
}
</style>
