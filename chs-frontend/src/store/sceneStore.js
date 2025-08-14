import { defineStore } from 'pinia';

export const useSceneStore = defineStore('scene', {
  state: () => ({
    scenes: {
      1: [ // Project ID
        { id: 101, name: 'Dam Overflow Test', mode: 'SIL' },
        { id: 102, name: 'Pump Station Stress Test', mode: 'HIL' },
      ],
      2: [
        { id: 201, name: 'Canal Flow Optimization', mode: 'SIL' },
      ]
    },
  }),
  getters: {
    getScenesByProjectId: (state) => (projectId) => {
      return state.scenes[projectId] || [];
    },
  },
  actions: {
    async createScene(projectId, scene) {
      if (!this.scenes[projectId]) {
        this.scenes[projectId] = [];
      }
      const newScene = { ...scene, id: Date.now() };
      this.scenes[projectId].push(newScene);
    },
  },
});
