<template>
  <a-list item-layout="horizontal" :data-source="alarms">
    <template #renderItem="{ item }">
      <a-list-item class="alarm-item" @click="onAlarmClick(item)">
        <a-list-item-meta>
          <template #title>
            <a-tag :color="item.severity === 'high' ? 'volcano' : 'orange'">
              {{ item.severity.toUpperCase() }}
            </a-tag>
            {{ item.title }}
          </template>
          <template #description>
            {{ item.description }}
          </template>
        </a-list-item-meta>
      </a-list-item>
    </template>
  </a-list>
</template>

<script setup>
import { ref } from 'vue';

const alarms = ref([
  { id: 'alarm-001', agentId: 'res-a', severity: 'high', title: 'Reservoir Level Critical', description: 'Reservoir A level is at 99.5m, exceeding the 99m limit.' },
  { id: 'alarm-002', agentId: 'pump-b', severity: 'medium', title: 'Pump Overload Warning', description: 'Pump Station B is operating at 110% capacity.' },
  { id: 'alarm-003', agentId: 'gate-c', severity: 'medium', title: 'Flow Rate Anomaly', description: 'Pipeline C has an unexpected drop in flow rate.' },
]);

const emit = defineEmits(['alarm-selected']);

const onAlarmClick = (alarm) => {
  emit('alarm-selected', alarm);
};
</script>

<style scoped>
.alarm-item {
  cursor: pointer;
  transition: background-color 0.3s;
}

.alarm-item:hover {
  background-color: #f0f2f5;
}
</style>
