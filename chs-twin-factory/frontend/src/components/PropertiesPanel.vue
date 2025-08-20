<template>
    <div class="properties-panel flex-grow">
        <div v-if="selectedNode" class="p-4 bg-gray-50 rounded-lg border space-y-3">
            <h3 class="font-bold text-lg">{{ selectedNode.label }}</h3>
            <div v-if="selectedNode.data.params && Object.keys(selectedNode.data.params).length > 0">
                <div v-for="(value, key) in selectedNode.data.params" :key="key" class="space-y-1">
                    <label class="block text-sm font-medium text-gray-600">{{ key }}</label>
                    <input type="number" step="0.01" v-model.number="selectedNode.data.params[key]"
                        class="w-full p-1.5 border rounded-md text-sm">
                </div>
            </div>
            <div v-else class="text-sm text-gray-500">无可用参数</div>
        </div>
        <div v-else
            class="text-sm text-gray-500 p-4 bg-gray-50 rounded-lg border h-full flex items-center justify-center">
            <p>在画布中选择一个模块以编辑其属性</p>
        </div>
    </div>
</template>

<script setup>
defineProps({
    selectedNode: Object,
});
</script>