<template>
  <a-list item-layout="horizontal" :data-source="decisions">
    <template #renderItem="{ item }">
      <a-list-item>
        <a-list-item-meta :description="item.description">
          <template #title>
            {{ item.title }}
          </template>
        </a-list-item-meta>
        <template #actions>
          <a-button type="primary" size="small" @click="handleConfirm(item)">Confirm</a-button>
          <a-button type="default" size="small" danger @click="handleReject(item)">Reject</a-button>
        </template>
      </a-list-item>
    </template>
  </a-list>
</template>

<script setup>
import { ref } from 'vue';
import { message } from 'ant-design-vue';

const decisions = ref([
  { id: 'dec-001', title: 'Increase pump speed at Station A', description: 'System suggests increasing pump speed to 1200 RPM to meet demand.' },
  { id: 'dec-002', title: 'Open Gate B by 15%', description: 'To regulate downstream flow, system suggests opening Gate B by an additional 15%.' },
  { id: 'dec-003', title: 'Divert flow to Reservoir C', description: 'High inflow detected. System suggests diverting 20% of flow to Reservoir C.' },
]);

const handleConfirm = (decision) => {
  message.success(`Confirmed: ${decision.title}`);
  // Here you would typically call a store action or API
  removeDecision(decision.id);
};

const handleReject = (decision) => {
  message.warning(`Rejected: ${decision.title}`);
  // Here you would typically call a store action or API
  removeDecision(decision.id);
};

const removeDecision = (id) => {
  decisions.value = decisions.value.filter(d => d.id !== id);
};
</script>

<style scoped>
</style>
