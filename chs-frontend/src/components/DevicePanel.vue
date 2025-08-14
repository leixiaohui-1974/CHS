<template>
  <div class="device-panel">
    <h3>Available Edge Devices</h3>
    <div
      v-for="device in devices"
      :key="device.id"
      class="device-item"
      @drop="() => onDrop(device)"
      @dragover.prevent
    >
      <p><b>{{ device.name }}</b> ({{ device.role }})</p>
      <p>IP: {{ device.ip }} | Status: <a-tag :color="device.status === 'Online' ? 'green' : 'volcano'">{{ device.status }}</a-tag></p>
      <div v-if="getDeployedAgent(device.id)" class="deployed-agent">
        Deployed: {{ getDeployedAgent(device.id).type }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { storeToRefs } from 'pinia';
import { useDeviceStore } from '../store/deviceStore';

const props = defineProps({
  deployments: {
    type: Object,
    required: true,
  },
  agents: {
    type: Array,
    required: true,
  }
});

const emit = defineEmits(['deploy-agent']);

const deviceStore = useDeviceStore();
const { devices } = storeToRefs(deviceStore);

const onDrop = (device) => {
  const agentId = event.dataTransfer.getData('agentId');
  if (agentId) {
    emit('deploy-agent', { agentId, deviceId: device.id });
  }
};

const getDeployedAgent = (deviceId) => {
  const agentId = Object.keys(props.deployments).find(key => props.deployments[key] === deviceId);
  if (!agentId) return null;
  return props.agents.find(a => a.id == agentId);
};
</script>

<style scoped>
.device-panel {
  position: absolute;
  right: 16px;
  top: 80px;
  width: 300px;
  max-height: 70vh;
  overflow-y: auto;
  background: white;
  z-index: 1000;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}
.device-item {
  padding: 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  margin-bottom: 8px;
  background: #fafafa;
}
.deployed-agent {
  margin-top: 8px;
  padding: 4px;
  background: #e6f7ff;
  border: 1px solid #91d5ff;
  border-radius: 4px;
  text-align: center;
}
</style>
