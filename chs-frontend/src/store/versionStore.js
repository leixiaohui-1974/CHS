import { defineStore } from 'pinia';

export const useVersionStore = defineStore('version', {
  state: () => ({
    // Each key is a sceneId, and the value is an array of version snapshots.
    versions: {},
  }),
  getters: {
    getVersionsBySceneId: (state) => (sceneId) => {
      return state.versions[sceneId] || [];
    },
  },
  actions: {
    createCommit({ sceneId, message, config }) {
      if (!this.versions[sceneId]) {
        this.versions[sceneId] = [];
      }

      const newCommit = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        message,
        config: JSON.parse(JSON.stringify(config)), // Deep copy of the config
      };

      // Add to the beginning of the array so the newest is first
      this.versions[sceneId].unshift(newCommit);
    },
  },
});
