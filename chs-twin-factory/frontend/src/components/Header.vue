<template>
    <header class="flex items-center justify-between p-2 bg-white border-b shadow-sm flex-shrink-0 z-10">
        <h1 class="text-xl font-bold text-blue-700">CHS Twin Factory</h1>
        <div class="flex items-center space-x-3">
            <div class="flex items-center space-x-2">
                <label for="sim-duration" class="text-sm font-medium">仿真时长 (s):</label>
                <input type="number" id="sim-duration" :value="duration"
                    @input="$emit('update:duration', Number($event.target.value))"
                    class="w-24 p-1 border rounded-md text-sm">
            </div>
            <button @click="$emit('runSimulation')" :disabled="isRunning"
                class="px-3 py-1.5 bg-green-500 text-white rounded-md hover:bg-green-600 transition shadow-sm disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center space-x-1">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                        clip-rule="evenodd" />
                </svg>
                <span>前端仿真</span>
            </button>
            <button @click="$emit('resetSimulation')"
                class="px-3 py-1.5 bg-gray-500 text-white rounded-md hover:bg-gray-600 transition shadow-sm flex items-center space-x-1">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1zm4 0a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z"
                        clip-rule="evenodd" />
                </svg>
                <span>重置</span>
            </button>
            <div class="flex items-center space-x-2 pl-4 border-l">
                <span class="text-sm font-medium">仿真时间:</span>
                <span class="font-mono p-1.5 text-sm bg-gray-100 rounded-md w-24 text-center">{{ currentTime.toFixed(2)
                    }} s</span>
            </div>
        </div>
    </header>
</template>

<script setup>
defineProps({
    isRunning: Boolean,
    duration: Number,
    currentTime: Number,
});
defineEmits(['runSimulation', 'resetSimulation', 'update:duration']);
</script>