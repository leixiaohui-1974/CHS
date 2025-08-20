<template>
    <div class="ai-training-panel flex flex-col flex-grow space-y-4">
        <div class="p-4 bg-gray-50 rounded-lg border space-y-3">
            <h3 class="font-bold text-lg">AI 智能体训练</h3>
            <div>
                <label class="block text-sm font-medium text-gray-600">实验名称</label>
                <input type="text" v-model="trainingConfig.name" class="mt-1 w-full p-1.5 border rounded-md text-sm">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-600">选择算法</label>
                <select v-model="trainingConfig.algorithm" class="mt-1 w-full p-1.5 border rounded-md text-sm">
                    <option>PPO</option>
                    <option>SAC</option>
                </select>
            </div>
            <div v-if="trainingConfig.algorithm === 'PPO'">
                <label class="block text-sm font-medium text-gray-600">学习率 (Learning Rate)</label>
                <input type="number" step="0.00001" v-model.number="trainingConfig.hyperparams.learning_rate"
                    class="mt-1 w-full p-1.5 border rounded-md text-sm">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-600">总训练步数 (Total Timesteps)</label>
                <input type="number" step="1000" v-model.number="trainingConfig.hyperparams.total_timesteps"
                    class="mt-1 w-full p-1.5 border rounded-md text-sm">
            </div>
            <button @click="startBackendTraining" :disabled="trainingState.isRunning"
                class="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition shadow-sm disabled:bg-gray-400">
                🚀 {{ trainingState.isRunning ? '训练中...' : '启动后端训练' }}
            </button>
        </div>
        <div class="p-4 bg-gray-900 text-white rounded-lg border flex-grow flex flex-col min-h-0">
            <h3 class="font-bold text-lg mb-2 text-gray-200">训练监控</h3>
            <div class="flex-grow min-h-0">
                <canvas ref="trainingChartCanvas"></canvas>
            </div>
            <div class="mt-4 flex-shrink-0 h-32 bg-black rounded p-2 overflow-y-auto font-mono text-xs">
                <div v-for="(log, index) in trainingState.logs" :key="index">{{ log }}</div>
                <div v-if="trainingState.isRunning && trainingState.logs.length === 0" class="animate-pulse">Awaiting
                    logs...</div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import useAITraining from '../composables/useAITraining';

const props = defineProps({
    modelGraph: Object,
});

const trainingChartCanvas = ref(null);
const {
    trainingConfig,
    trainingState,
    startBackendTraining,
    initializeChart
} = useAITraining(props.modelGraph, trainingChartCanvas);

onMounted(() => {
    initializeChart();
});
</script>