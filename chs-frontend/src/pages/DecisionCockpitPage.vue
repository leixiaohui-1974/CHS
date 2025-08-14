<template>
  <div class="cockpit-container">
    <!-- KPIs Section -->
    <a-row :gutter="[16, 16]">
      <a-col :span="24">
        <a-card title="System KPIs">
          <template #extra>
            <a-button type="text" @click="showSettingsModal">
              <template #icon><setting-outlined /></template>
            </a-button>
          </template>
          <a-row>
            <a-col :span="6">
              <a-statistic title="System Efficiency" :value="98.5" :precision="1" suffix="%" />
            </a-col>
            <a-col :span="6">
              <a-statistic title="Water Level" :value="112.8" :precision="1" suffix="m" />
            </a-col>
            <a-col :span="6">
              <a-statistic title="Active Alarms" :value="3" />
            </a-col>
            <a-col :span="6">
              <a-statistic title="Energy Consumption" :value="1.2" :precision="2" suffix="MWh" />
            </a-col>
          </a-row>
        </a-card>
      </a-col>
    </a-row>

    <!-- Main Content Area -->
    <a-row :gutter="[16, 16]" style="margin-top: 16px;">
      <!-- Left Column -->
      <a-col :span="8">
        <a-card title="System Alarms" style="margin-bottom: 16px;">
          <system-alarms @alarm-selected="handleAlarmSelected" />
        </a-card>
        <a-card title="Decision Instruction Stream">
          <decision-stream />
        </a-card>
      </a-col>

      <!-- Right Column -->
      <a-col :span="16">
        <a-card title="System Map Visualization">
          <div style="height: 600px; width: 100%;">
            <l-map ref="map" v-model:zoom="zoom" :center="center">
              <l-tile-layer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                layer-type="base"
                name="OpenStreetMap"
              ></l-tile-layer>
              <l-marker v-for="marker in markers" :key="marker.id" :lat-lng="marker.latlng">
                <l-popup>{{ marker.popupText }}</l-popup>
              </l-marker>
            </l-map>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <!-- Agent Interaction Modal -->
    <a-modal
      v-model:open="isPanelVisible"
      :title="'Agent Interaction: ' + (selectedAgent ? selectedAgent.type : '')"
      width="700px"
      :footer="null"
      @cancel="handlePanelClose"
    >
      <agent-interaction-panel
        v-if="selectedAgent"
        :selected-agent="selectedAgent"
        :is-simulation-running="true"
        scene-mode="SIL"
      />
    </a-modal>

    <!-- Settings Modal -->
    <a-modal
      v-model:open="isSettingsVisible"
      title="Configure Intervention Level"
      @ok="handleSettingsOk"
    >
      <p>Select the desired level of system autonomy and human oversight.</p>
      <a-radio-group v-model:value="interventionLevel" button-style="solid">
        <a-radio-button value="full_review">全面审核 (Full Review)</a-radio-button>
        <a-radio-button value="key_events_review">重要事项审核 (Key Events)</a-radio-button>
        <a-radio-button value="exception_intervention">异常时介入 (Exception)</a-radio-button>
        <a-radio-button value="full_autonomy">完全自主 (Full Autonomy)</a-radio-button>
      </a-radio-group>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import "leaflet/dist/leaflet.css";
import { LMap, LTileLayer, LMarker, LPopup } from "@vue-leaflet/vue-leaflet";
import { SettingOutlined } from '@ant-design/icons-vue';
import { storeToRefs } from 'pinia';
import { useSettingsStore } from '../store/settingsStore';
import SystemAlarms from '../components/SystemAlarms.vue';
import DecisionStream from '../components/DecisionStream.vue';
import AgentInteractionPanel from '../components/AgentInteractionPanel.vue';

const zoom = ref(10);
const center = ref([30.5, 114.3]); // Default center, e.g., Wuhan
const markers = ref([
  { id: 'res-a', latlng: [30.55, 114.35], popupText: 'Reservoir A' },
  { id: 'pump-b', latlng: [30.45, 114.25], popupText: 'Pump Station B' },
  { id: 'gate-c', latlng: [30.50, 114.40], popupText: 'Gate C' },
]);

const mockAgents = {
  'res-a': { id: 'res-a', type: 'Reservoir', config: { 'maxLevel': 99, 'minLevel': 80 } },
  'pump-b': { id: 'pump-b', type: 'Pump', config: { 'maxSpeed': 1500, 'minSpeed': 300, 'power': 500 } },
  'gate-c': { id: 'gate-c', type: 'Gate', config: { 'openPercentage': 45, 'manualControl': false } },
};

const selectedAgent = ref(null);
const isPanelVisible = ref(false);

const handleAlarmSelected = (alarm) => {
  const agent = mockAgents[alarm.agentId];
  if (agent) {
    selectedAgent.value = agent;
    isPanelVisible.value = true;
  }
};

const handlePanelClose = () => {
  isPanelVisible.value = false;
  selectedAgent.value = null;
};

// Settings Modal Logic
const settingsStore = useSettingsStore();
const { interventionLevel } = storeToRefs(settingsStore);
const isSettingsVisible = ref(false);

const showSettingsModal = () => {
  isSettingsVisible.value = true;
};

const handleSettingsOk = () => {
  isSettingsVisible.value = false;
  // The value is already bound to the store, so no extra action is needed.
};
</script>

<style scoped>
.cockpit-container {
  padding: 24px;
  height: 100%;
}
</style>
