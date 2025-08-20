<template>
    <section class="flex-grow relative" ref="flowContainer" @drop="onDrop" @dragover.prevent @dragenter.prevent>
        <VueFlow :model-value="elements" @update:model-value="onElementsUpdate" :fit-view-on-init="true"
            @node-click="onNodeClick" @pane-click="onPaneClick" @connect="onConnect" @edges-change="onEdgesChange">
            <Background />
            <Controls />
            <template #node-custom="{ data, label, selected }">
                <div class="p-3 border-2 rounded-lg shadow-md bg-white w-48 transition"
                    :class="{ 'border-blue-500 shadow-lg': selected }">
                    <div class="font-bold text-center mb-2 text-sm">{{ label }}</div>
                    <div v-if="data.params && Object.keys(data.params).length > 0"
                        class="text-xs text-gray-600 space-y-1">
                        <div v-for="(value, key) in data.params" :key="key" class="flex justify-between">
                            <span>{{ key }}:</span>
                            <span class="font-mono">{{ formatValue(value) }}</span>
                        </div>
                    </div>
                    <div class="mt-2 text-center text-blue-600 font-bold text-lg font-mono">
                        {{ formatValue(data.output, 3) }}
                    </div>
                </div>
            </template>
        </VueFlow>
    </section>
</template>

<script setup>
import { ref } from 'vue';
import { VueFlow, useVueFlow } from '@vue-flow/core';
import { Background } from '@vue-flow/background';
import { Controls } from '@vue-flow/controls';
import { availableNodes, getNodeDefaultParams, getNodeHandles } from '../composables/useVueFlow';
import useVueFlowManager from '../composables/useVueFlow';

const props = defineProps({
    elements: Array,
});
const emit = defineEmits(['update:elements', 'nodeSelected']);

const { onConnect, onEdgesChange } = useVueFlowManager();

const flowContainer = ref(null);
const { project, addNodes } = useVueFlow();

let nodeId = 0;

const onDrop = (event) => {
    const type = event.dataTransfer?.getData('application/vueflow');
    if (!type) return;

    const { left, top } = flowContainer.value.getBoundingClientRect();
    const position = project({ x: event.clientX - left, y: event.clientY - top });

    const nodeInfo = availableNodes.find(n => n.type === type);
    if (!nodeInfo) return;

    const newNode = {
        id: `node_${nodeId++}`,
        type: 'custom',
        position,
        label: nodeInfo.label,
        data: {
            type: nodeInfo.type,
            params: getNodeDefaultParams(type),
            output: 0,
            inputs: {},
        },
        ...getNodeHandles(type)
    };
    addNodes([newNode]);
};

const onNodeClick = (event) => emit('nodeSelected', event.node);
const onPaneClick = () => emit('nodeSelected', null);

const onElementsUpdate = (updatedElements) => {
    emit('update:elements', updatedElements);
}

const formatValue = (value, precision = 2) => {
    if (typeof value !== 'number') return 'N/A';
    return value.toFixed(precision);
};
</script>