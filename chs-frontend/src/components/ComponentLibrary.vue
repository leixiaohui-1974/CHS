<template>
  <div class="component-library">
    <h3>Component Library</h3>
    <div class="component-item" draggable="true" @dragstart="onDragStart('OntologySimulationAgent')">
      Ontology Simulation Agent
    </div>
    <div class="component-item" draggable="true" @dragstart="onDragStart('SensingControlAgent')">
      Sensing/Control Agent
    </div>
    <div class="component-item" draggable="true" @dragstart="onDragStart('DisturbanceAgent')">
      Disturbance Agent
    </div>
  </div>
</template>

<script setup>
const onDragStart = (agentType) => {
  event.dataTransfer.setData('agentType', agentType);
};
</script>

<style scoped>
.component-library {
  padding: 16px;
  background-color: #f0f2f5;
  height: 100%;
}
.component-item {
  padding: 8px;
  margin-bottom: 8px;
  background-color: #fff;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  cursor: grab;
  text-align: center;
}
</style>
