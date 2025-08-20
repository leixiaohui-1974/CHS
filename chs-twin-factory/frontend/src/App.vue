<template>
    <div class="flex flex-col h-screen w-screen text-gray-800 font-sans">
        <Header @run-simulation="runFrontendSimulation" @reset-simulation="resetSimulation"
            :is-running="simulationState.isRunning" v-model:duration="simulationConfig.duration"
            :current-time="simulationState.currentTime" />
        <main class="flex flex-grow overflow-hidden">
            <Sidebar />
            <Canvas :elements="elements" @update:elements="updateElements" @node-selected="onNodeSelected" />
            <aside class="w-96 bg-white p-4 border-l flex flex-col space-y-4 flex-shrink-0 overflow-y-auto">
                <div>
                    <div class="border-b border-gray-200">
                        <nav class="-mb-px flex space-x-6" aria-label="Tabs">
                            <button @click="activeTab = 'properties'" :class="tabClass('properties')">属性</button>
                            <button @click="activeTab = 'ai_training'" :class="tabClass('ai_training')">AI训练</button>
                            <button @click="activeTab = 'analysis'" :class="tabClass('analysis')">分析</button>
                        </nav>
                    </div>
                </div>
                <PropertiesPanel v-show="activeTab === 'properties'" :selected-node="selectedNode" />
                <AITrainingPanel v-show="activeTab === 'ai_training'" :model-graph="serializableGraph" />

                <!-- Placeholder for new panels -->
                <div v-show="activeTab === 'analysis'" class="p-4 bg-gray-50 rounded-lg border h-full">
                    <h3 class="font-bold text-lg mb-2">高级分析面板</h3>
                    <p class="text-sm text-gray-600">
                        这里将放置用于**预测 (Prediction)**, **辨识 (Identification)**, 和 **调度 (Dispatch)** 的高级功能组件。
                    </p>
                </div>

            </aside>
        </main>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import Header from './components/Header.vue';
import Sidebar from './components/Sidebar.vue';
import Canvas from './components/Canvas.vue';
import PropertiesPanel from './components/PropertiesPanel.vue';
import AITrainingPanel from './components/AITrainingPanel.vue';

import useVueFlowManager from './composables/useVueFlow';
import useSimulation from './composables/useSimulation';

const activeTab = ref('properties');
const { elements, selectedNode, onNodeSelected, updateElements } = useVueFlowManager();
const {
    simulationConfig,
    simulationState,
    runFrontendSimulation,
    resetSimulation
} = useSimulation(elements);

const serializableGraph = computed(() => ({
    nodes: elements.value.filter(el => el.position).map(n => ({ id: n.id, type: n.data.type, params: n.data.params })),
    edges: elements.value.filter(el => el.source).map(e => ({ source: e.source, target: e.target, sourceHandle: e.sourceHandle, targetHandle: e.targetHandle })),
}));

const tabClass = (tabName) => [
    'whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm',
    activeTab.value === tabName
        ? 'border-blue-500 text-blue-600'
        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
];
</script>