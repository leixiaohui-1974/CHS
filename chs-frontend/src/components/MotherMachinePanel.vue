<template>
  <div class="mother-machine-panel" v-if="selectedAgent">
    <h4>Mother Machine: {{ selectedAgent.type }}</h4>
    <p>ID: {{ selectedAgent.id }}</p>
    <a-button @click="runAutonomousCognition" :loading="isLoading">
      Autonomous Cognition
    </a-button>
    <a-button @click="runPidGeneration" :loading="isLoading" style="margin-left: 8px;">
      Auto-generate PID
    </a-button>
    <div v-if="result" class="result-display">
      <h5>Result:</h5>
      <pre>{{ result }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const props = defineProps({
  selectedAgent: {
    type: Object,
    default: null,
  },
});

const isLoading = ref(false);
const result = ref(null);

const runAutonomousCognition = async () => {
  if (!props.selectedAgent) return;
  isLoading.value = true;
  result.value = null;
  // Mock API call
  await new Promise(resolve => setTimeout(resolve, 1500));
  result.value = { cognition_status: 'Completed', identified_parameters: { p: 1.2, i: 0.5, d: 0.1 } };
  // Here we would emit an event to update the agent in the parent component
  isLoading.value = false;
};

const runPidGeneration = async () => {
  if (!props.selectedAgent) return;
  isLoading.value = true;
  result.value = null;
  // Mock API call
  await new Promise(resolve => setTimeout(resolve, 1500));
  result.value = { pid_gains: { Kp: 2.0, Ki: 0.8, Kd: 0.3 } };
  isLoading.value = false;
};
</script>

<style scoped>
.mother-machine-panel {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  background: white;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  width: 500px;
}
.result-display {
  margin-top: 16px;
  background-color: #f0f2f5;
  padding: 8px;
  border-radius: 4px;
}
</style>
