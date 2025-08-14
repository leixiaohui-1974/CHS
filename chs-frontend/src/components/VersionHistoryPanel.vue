<template>
  <a-drawer
    :open="open"
    title="Version History"
    placement="right"
    width="600"
    @close="onClose"
  >
    <a-list
      v-if="versions.length"
      :data-source="versions"
      item-layout="horizontal"
    >
      <template #renderItem="{ item }">
        <a-list-item class="version-item" @click="selectedVersion = item">
          <a-list-item-meta>
            <template #title>
              <a>{{ item.message }}</a>
            </template>
            <template #description>
              {{ new Date(item.timestamp).toLocaleString() }}
            </template>
          </a-list-item-meta>
        </a-list-item>
      </template>
    </a-list>
    <a-empty v-else description="No versions yet. Save the scene to create one." />

    <div v-if="selectedVersion" class="version-details">
      <a-divider />
      <h4>Details for version: {{ selectedVersion.message }}</h4>
      <p><strong>Timestamp:</strong> {{ new Date(selectedVersion.timestamp).toLocaleString() }}</p>
      <a-button @click="revertToVersion" type="primary" danger>
        Revert to this version
      </a-button>
      <pre>{{ JSON.stringify(selectedVersion.config, null, 2) }}</pre>
    </div>
  </a-drawer>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useVersionStore } from '../store/versionStore';
import { message } from 'ant-design-vue';

const props = defineProps({
  sceneId: {
    type: [Number, String],
    required: true,
  },
  open: {
    type: Boolean,
    required: true,
  },
});

const emit = defineEmits(['close', 'revert']);

const versionStore = useVersionStore();

const versions = computed(() => versionStore.getVersionsBySceneId(props.sceneId));
const selectedVersion = ref(null);

const onClose = () => {
  emit('close');
};

const revertToVersion = () => {
  if (!selectedVersion.value) return;
  // This emits the full config object of the selected version.
  // The parent component is responsible for applying this state.
  emit('revert', selectedVersion.value.config);
  message.success(`Reverted to version: "${selectedVersion.value.message}"`);
  onClose();
};
</script>

<style scoped>
.version-item {
  cursor: pointer;
  padding: 12px 8px;
}
.version-item:hover {
  background-color: #f0f2f5;
}
.version-details {
  margin-top: 24px;
}
pre {
  background-color: #fafafa;
  padding: 16px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  max-height: 400px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
