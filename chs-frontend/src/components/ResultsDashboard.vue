<template>
  <div class="results-dashboard">
    <h4>SIL Simulation Results</h4>
    <div v-if="!isConnected">
      <a-spin /> Connecting to simulation...
    </div>
    <div v-else>
      <p>Status: {{ connectionStatus }}</p>
      <div class="log-container">
        <p v-for="(message, index) in messages" :key="index">{{ message }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const messages = ref([]);
const isConnected = ref(false);
const connectionStatus = ref('Connected');
let mockSocket;

onMounted(() => {
  // Mock WebSocket connection
  mockSocket = setInterval(() => {
    const timestamp = new Date().toLocaleTimeString();
    messages.value.push(`[${timestamp}] Water level: ${(Math.random() * 10 + 5).toFixed(2)}m`);
    if (messages.value.length > 10) {
      messages.value.shift();
    }
  }, 2000);
  isConnected.value = true;
});

onUnmounted(() => {
  clearInterval(mockSocket);
});
</script>

<style scoped>
.results-dashboard {
  position: absolute;
  bottom: 16px;
  right: 16px;
  width: 350px;
  height: 300px;
  background: white;
  z-index: 1000;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
}
.log-container {
  flex-grow: 1;
  overflow-y: auto;
  background-color: #f0f2f5;
  padding: 8px;
  border-radius: 4px;
  margin-top: 8px;
}
</style>
