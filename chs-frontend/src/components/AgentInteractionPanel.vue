<template>
  <div class="agent-interaction-panel" v-if="selectedAgent">
    <h4>Agent: {{ selectedAgent.type }} (ID: {{ selectedAgent.id }})</h4>
    <a-tabs v-model:activeKey="activeKey">
      <a-tab-pane key="1" tab="Configuration">
        <div v-if="selectedAgent.config && Object.keys(selectedAgent.config).length > 0">
          <a-form layout="vertical">
            <a-form-item v-for="key in Object.keys(selectedAgent.config)" :key="key" :label="key">
              <a-switch
                v-if="typeof selectedAgent.config[key] === 'boolean'"
                v-model:checked="selectedAgent.config[key]"
              />
              <a-input-number
                v-else-if="typeof selectedAgent.config[key] === 'number'"
                v-model:value="selectedAgent.config[key]"
                style="width: 100%;"
              />
              <a-input
                v-else
                v-model:value="selectedAgent.config[key]"
              />
            </a-form-item>
          </a-form>
        </div>
        <a-empty v-else description="This agent has no configurable parameters." />

        <a-divider />
        <p>Add a new parameter:</p>
        <div class="add-param-form">
            <a-input v-model:value="newParam.key" placeholder="Parameter Name" />
            <a-input v-model:value="newParam.value" placeholder="Parameter Value" style="margin-left: 8px;" />
            <a-button @click="addParameter" type="primary" style="margin-left: 8px;">Add</a-button>
        </div>
      </a-tab-pane>
      <a-tab-pane key="2" tab="Monitoring">
        <div class="monitoring-container">
            <div class="readouts">
                <a-statistic title="Current Water Level" :value="latestValue" :precision="2" suffix="m" />
            </div>
            <v-chart class="chart" :option="chartOption" autoresize />
        </div>
      </a-tab-pane>
      <a-tab-pane key="3" tab="Manual Control">
        <div v-if="!isSimulationRunning || sceneMode !== 'SIL'">
            <a-alert
                message="Manual Control Not Available"
                description="Manual control is only available during an active SIL (Software-in-the-Loop) simulation."
                type="info"
                show-icon
            />
        </div>
        <div v-else>
            <div class="manual-control-row">
                <span>Manual Override</span>
                <a-switch v-model:checked="isManualOverride" />
            </div>
            <p v-if="isManualOverride" class="manual-desc">
                Autonomous agent behavior is now paused. You can manually input output values below.
            </p>
            <div v-if="isManualOverride" class="manual-input-row">
                <a-input-number v-model:value="manualValue" placeholder="Enter value" style="flex-grow: 1;" />
                <a-button @click="submitManualValue" type="primary" style="margin-left: 8px;">Submit</a-button>
            </div>
        </div>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script setup>
import { ref, watch, reactive, onUnmounted, computed } from 'vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components';
import VChart from 'vue-echarts';
import { message } from 'ant-design-vue';

// Register echarts components
use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
]);

const props = defineProps({
  selectedAgent: {
    type: Object,
    default: null,
  },
  isSimulationRunning: {
    type: Boolean,
    default: false,
  },
  sceneMode: {
    type: String,
    default: 'SIL',
  }
});

const activeKey = ref('1');
const newParam = reactive({ key: '', value: '' });

// --- Monitoring State ---
const monitoringData = ref([]);
const latestValue = computed(() => monitoringData.value.length > 0 ? monitoringData.value[monitoringData.value.length - 1][1] : 0);
let simulationInterval = null;
let time = 0;

const chartOption = ref({
  tooltip: {
    trigger: 'axis'
  },
  xAxis: {
    type: 'time',
  },
  yAxis: {
    type: 'value',
    name: 'Water Level (m)',
    min: 80,
    max: 120,
  },
  series: [
    {
      data: monitoringData,
      type: 'line',
      showSymbol: false,
      name: 'Water Level'
    },
  ],
});

// --- Manual Control State ---
const isManualOverride = ref(false);
const manualValue = ref(0);

const submitManualValue = async () => {
    if (props.selectedAgent) {
        console.log(`MANUAL OVERRIDE for agent ${props.selectedAgent.id}: Submitting value ${manualValue.value}`);
        // Mock API call
        await new Promise(resolve => setTimeout(resolve, 500));
        message.success(`Manual value ${manualValue.value} submitted for agent ${props.selectedAgent.id}.`);
    }
};

const addParameter = () => {
    if (newParam.key && props.selectedAgent) {
        if (!props.selectedAgent.config) {
            props.selectedAgent.config = {};
        }
        const numValue = parseFloat(newParam.value);
        props.selectedAgent.config[newParam.key] = isNaN(numValue) ? newParam.value : numValue;
        newParam.key = '';
        newParam.value = '';
    }
};


// --- Monitoring Simulation Logic ---
const startMonitoring = () => {
  if (simulationInterval) return; // Already running
  time = 0;
  monitoringData.value = []; // Reset data
  simulationInterval = setInterval(() => {
    time++;
    const baseLevel = 100;
    const variation = 10 * Math.sin(time * 0.5);
    const noise = (Math.random() - 0.5) * 2;
    const newValue = baseLevel + variation + noise;

    const now = new Date();
    monitoringData.value.push([now.getTime(), newValue]);

    if (monitoringData.value.length > 100) {
      monitoringData.value.shift();
    }
  }, 1000);
};

const stopMonitoring = () => {
  if (simulationInterval) {
    clearInterval(simulationInterval);
    simulationInterval = null;
  }
};


// --- Lifecycle and Watchers ---
watch(() => [props.selectedAgent, activeKey.value], ([newAgent, newKey], [oldAgent, oldKey]) => {
    if (newAgent && newKey === '2') {
        startMonitoring();
    } else {
        stopMonitoring();
    }
});

// Reset tab and manual override when agent changes
watch(() => props.selectedAgent, (newAgent, oldAgent) => {
    if (newAgent !== oldAgent) {
        activeKey.value = '1';
        isManualOverride.value = false;
    }
});

// Cleanup on unmount
onUnmounted(() => {
  stopMonitoring();
});

</script>

<style scoped>
.agent-interaction-panel {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  background: white;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  width: 600px;
  max-width: 90vw;
}
.add-param-form {
    display: flex;
    align-items: center;
}
.monitoring-container {
    display: flex;
    flex-direction: column;
    gap: 16px;
}
.readouts {
    display: flex;
    gap: 24px;
}
.chart {
  height: 300px;
}
.manual-control-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 16px;
}
.manual-desc {
    color: #888;
    margin-top: 8px;
    margin-bottom: 16px;
}
.manual-input-row {
    display: flex;
    align-items: center;
}
</style>
