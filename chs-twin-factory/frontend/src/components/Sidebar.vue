<template>
    <aside class="w-64 bg-white p-4 border-r overflow-y-auto flex-shrink-0">
        <h2 class="text-lg font-semibold mb-4">模块库</h2>
        <div class="space-y-3">
            <div v-for="node in availableNodes" :key="node.type"
                class="p-3 border rounded-lg shadow-sm bg-gray-50 hover:shadow-md hover:bg-blue-50 transition cursor-grab"
                draggable="true" @dragstart="onDragStart($event, node.type)">
                <h3 class="font-bold text-gray-700">{{ node.label }}</h3>
                <p class="text-xs text-gray-500">{{ node.description }}</p>
            </div>
        </div>
    </aside>
</template>

<script setup>
import { availableNodes } from '../composables/useVueFlow';

const onDragStart = (event, nodeType) => {
    if (event.dataTransfer) {
        event.dataTransfer.setData('application/vueflow', nodeType);
        event.dataTransfer.effectAllowed = 'move';
    }
};
</script>