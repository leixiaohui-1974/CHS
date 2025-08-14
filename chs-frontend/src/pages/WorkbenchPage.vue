<template>
  <a-layout class="workbench-layout">
    <a-layout-sider width="250" theme="light">
      <ComponentLibrary />
    </a-layout-sider>
    <a-layout>
      <div class="toolbar">
        <a-alert :message="`Current Scene ID: ${sceneId} | Mode: ${sceneMode.toUpperCase()}`" type="info" show-icon style="margin-bottom: 8px;" />
        <a-button @click="saveScene" type="primary">
          Save Scene
        </a-button>
        <a-button @click="() => isHistoryPanelVisible = true" style="margin-left: 8px;">
          Version History
        </a-button>
        <a-button @click="toggleConnectMode" :type="isConnectMode ? 'primary' : 'default'" :disabled="isHILMode" style="margin-left: 8px;">
          {{ isConnectMode ? 'Exit Connect Mode' : 'Create Connections' }}
        </a-button>
        <a-button @click="() => isDrawerVisible = true" style="margin-left: 8px;">
          View Config
        </a-button>
        <a-button v-if="!isHILMode" type="primary" @click="startSilSimulation" style="margin-left: 8px;" danger>
          Start SIL Simulation
        </a-button>
        <a-button v-else type="primary" @click="startHilSimulation" style="margin-left: 8px;" danger>
          Deploy and Start HIL
        </a-button>
      </div>
      <a-layout-content class="map-container" @drop="onDrop" @dragover.prevent>
        <l-map ref="mapRef" v-model:zoom="zoom" :center="[47.41322, -1.219482]" @mousemove="handleMouseMove" @click="handleMapClick">
          <l-tile-layer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" layer-type="base" name="OpenStreetMap" />
          <l-marker
            v-for="agent in agents"
            :key="agent.id"
            :lat-lng="agent.latLng"
            :draggable="isHILMode"
            @dragstart="(e) => onAgentDragStart(e, agent)"
            @click.stop="() => handleAgentClick(agent)"
          >
            <l-popup>
              <b>{{ agent.type }}</b><br>
              ID: {{ agent.id }} <br>
              Config: {{ agent.config }}
            </l-popup>
          </l-marker>
          <l-polyline v-if="!isHILMode" v-for="(conn, index) in connections" :key="`conn-${index}`" :lat-lngs="[conn.source.latLng, conn.target.latLng]" color="blue" />
          <l-polyline v-if="!isHILMode && tempLine.length > 0" :lat-lngs="tempLine" color="red" dash-array="5, 5" />
        </l-map>
        <AgentInteractionPanel
          :selected-agent="selectedAgent"
          :is-simulation-running="isSimulationRunning"
          :scene-mode="sceneMode"
        />
        <ResultsDashboard v-if="isSimulationRunning" />
        <DevicePanel v-if="isHILMode" :deployments="deployments" :agents="agents" @deploy-agent="handleDeployAgent" />
      </a-layout-content>
    </a-layout>
    <a-drawer title="Simulation Config" :open="isDrawerVisible" @close="() => isDrawerVisible = false" width="500">
      <pre>{{ configJson }}</pre>
    </a-drawer>
    <VersionHistoryPanel
      v-if="sceneId"
      :scene-id="sceneId"
      :open="isHistoryPanelVisible"
      @close="() => isHistoryPanelVisible = false"
      @revert="handleRevert"
    />
  </a-layout>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import "leaflet/dist/leaflet.css";
import { LMap, LTileLayer, LMarker, LPopup, LPolyline } from "@vue-leaflet/vue-leaflet";
import { useSceneStore } from '../store/sceneStore';
import { useVersionStore } from '../store/versionStore';
import ComponentLibrary from '../components/ComponentLibrary.vue';
import AgentInteractionPanel from '../components/AgentInteractionPanel.vue';
import ResultsDashboard from '../components/ResultsDashboard.vue';
import DevicePanel from '../components/DevicePanel.vue';
import VersionHistoryPanel from '../components/VersionHistoryPanel.vue';
import { message } from 'ant-design-vue';

// --- Deep Merge Utility ---
const isObject = (item) => (item && typeof item === 'object' && !Array.isArray(item));

const deepMerge = (target, ...sources) => {
  if (!sources.length) return target;
  const source = sources.shift();

  if (isObject(target) && isObject(source)) {
    for (const key in source) {
      if (key === 'agents' && Array.isArray(target.agents) && Array.isArray(source.agents)) {
        source.agents.forEach(sourceAgent => {
          const targetAgentIndex = target.agents.findIndex(t => t.id === sourceAgent.id);
          if (targetAgentIndex !== -1) {
            target.agents[targetAgentIndex] = deepMerge(target.agents[targetAgentIndex], sourceAgent);
          } else {
            target.agents.push(sourceAgent);
          }
        });
      } else if (isObject(source[key])) {
        if (!target[key]) Object.assign(target, { [key]: {} });
        deepMerge(target[key], source[key]);
      } else {
        Object.assign(target, { [key]: source[key] });
      }
    }
  }

  return deepMerge(target, ...sources);
};

const route = useRoute();
const sceneStore = useSceneStore();
const versionStore = useVersionStore();

const sceneId = ref(null);
const sceneMode = ref('SIL'); // Default to SIL
const isHILMode = computed(() => sceneMode.value === 'HIL');

const zoom = ref(6);
const mapRef = ref(null);
const agents = ref([]);
const connections = ref([]);
const deployments = ref({}); // { agentId: deviceId }
const isConnectMode = ref(false);
const sourceAgent = ref(null);
const tempLine = ref([]);
const isDrawerVisible = ref(false);
const isHistoryPanelVisible = ref(false);
const selectedAgent = ref(null);
const isSimulationRunning = ref(false);

// --- Scene Loading and Inheritance Logic ---
const loadSceneData = () => {
  const currentSceneId = parseInt(route.params.sceneId, 10);
  sceneId.value = currentSceneId;

  let currentScene = sceneStore.getSceneById(currentSceneId);
  if (!currentScene) {
    console.error("Scene not found!");
    return;
  }

  sceneMode.value = currentScene.mode;

  const inheritanceChain = [];
  while (currentScene) {
    inheritanceChain.push(currentScene);
    currentScene = currentScene.parentId ? sceneStore.getSceneById(currentScene.parentId) : null;
  }

  inheritanceChain.reverse();

  const finalConfig = deepMerge({}, ...inheritanceChain.map(s => s.config));

  // Populate workbench state. Ensure arrays are initialized.
  agents.value = finalConfig.agents ? JSON.parse(JSON.stringify(finalConfig.agents)) : [];

  // Connections need to be rehydrated from IDs to full agent objects
  const rehydratedConnections = (finalConfig.connections || []).map(conn => {
    const source = agents.value.find(a => a.id === conn.from);
    const target = agents.value.find(a => a.id === conn.to);
    return source && target ? { source, target } : null;
  }).filter(Boolean); // Filter out any nulls if agents weren't found

  connections.value = rehydratedConnections;
};

const handleRevert = (revertedConfig) => {
  // The reverted config becomes the new state of the workbench.
  // We need to re-populate the agents and rehydrate the connections.
  agents.value = revertedConfig.agents ? JSON.parse(JSON.stringify(revertedConfig.agents)) : [];
  const rehydratedConnections = (revertedConfig.connections || []).map(conn => {
    const source = agents.value.find(a => a.id === conn.from);
    const target = agents.value.find(a => a.id === conn.to);
    return source && target ? { source, target } : null;
  }).filter(Boolean);
  connections.value = rehydratedConnections;

  // We should also probably save this reverted state as a new version.
  saveScene(`Reverted to version from ${new Date().toLocaleString()}`);
};

watch(() => route.params.sceneId, (newId) => {
  if (newId) {
    loadSceneData();
  }
}, { immediate: true });

// --- Saving Logic ---
const saveScene = (commitMessageOverride) => {
    const commitMessage = commitMessageOverride || prompt("Enter a commit message for this version:", "Updated scene configuration");
    if (!commitMessage) {
        message.info('Save cancelled.');
        return;
    }

    const currentConfig = {
        agents: agents.value,
        connections: connections.value.map(c => ({ from: c.source.id, to: c.target.id }))
    };

    // 1. Update the scene's main config in the sceneStore
    sceneStore.updateSceneConfig(sceneId.value, currentConfig);

    // 2. Create a version commit in the versionStore
    versionStore.createCommit({
        sceneId: sceneId.value,
        message: commitMessage,
        config: currentConfig
    });

    if (!commitMessageOverride) {
      message.success(`Scene saved and new version created: "${commitMessage}"`);
    }
};

const startSilSimulation = () => {
  console.log("Starting SIL Simulation with the following config:");
  console.log(JSON.parse(configJson.value));
  isSimulationRunning.value = true;
};

const startHilSimulation = () => {
  console.log("Starting HIL Simulation with the following config:");
  console.log(JSON.parse(configJson.value));
  isSimulationRunning.value = true;
};

const toggleConnectMode = () => {
  isConnectMode.value = !isConnectMode.value;
  selectedAgent.value = null;
  sourceAgent.value = null;
  tempLine.value = [];
};

const handleAgentClick = (agent) => {
  if (isConnectMode.value) {
    if (!sourceAgent.value) {
      sourceAgent.value = agent;
    } else {
      if (sourceAgent.value.id !== agent.id) {
        connections.value.push({ source: sourceAgent.value, target: agent });
      }
      sourceAgent.value = null;
      tempLine.value = [];
    }
  } else {
    selectedAgent.value = agent;
  }
};

const handleMapClick = () => {
  if (!isConnectMode.value) {
    selectedAgent.value = null;
  }
};

const handleMouseMove = (event) => {
  if (isConnectMode.value && sourceAgent.value) {
    tempLine.value = [sourceAgent.value.latLng, event.latlng];
  }
};

const onDrop = (event) => {
  event.preventDefault();
  const agentType = event.dataTransfer.getData('agentType');
  if (!agentType) return;
  const map = mapRef.value.leafletObject;
  const latLng = map.containerPointToLatLng(map.mouseEventToContainerPoint(event));
  agents.value.push({
    id: Date.now(),
    type: agentType,
    latLng: [latLng.lat, latLng.lng],
    config: {},
  });
};

const onAgentDragStart = (event, agent) => {
  if (isHILMode.value) {
    event.dataTransfer.setData('agentId', agent.id);
  }
};

const handleDeployAgent = ({ agentId, deviceId }) => {
  deployments.value[agentId] = deviceId;
};

const configJson = computed(() => {
  const config = {
    agents: agents.value.map(a => ({ id: a.id, type: a.type, position: a.latLng, config: a.config })),
  };
  if (isHILMode.value) {
    config.deployments = deployments.value;
  } else {
    config.connections = connections.value.map(c => ({ from: c.source.id, to: c.target.id }));
  }
  return JSON.stringify(config, null, 2);
});
</script>

<style scoped>
.workbench-layout {
  height: calc(100vh - 32px); /* Adjust for parent layout margin */
}
.map-container {
  position: relative;
}
.toolbar {
  margin-bottom: 16px;
  background: white;
  padding: 16px;
  border-radius: 4px;
}
</style>
