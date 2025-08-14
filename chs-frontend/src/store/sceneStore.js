import { defineStore } from 'pinia';

// Helper function to build a tree from a flat list of scenes
const buildSceneTree = (scenes, parentId = null) => {
  return scenes
    .filter(scene => scene.parentId === parentId)
    .map(scene => ({
      ...scene,
      // Properties for Ant Design Tree component
      title: scene.name,
      key: scene.id,
      children: buildSceneTree(scenes, scene.id),
    }));
};

export const useSceneStore = defineStore('scene', {
  state: () => ({
    // Each scene now has a parentId and its own config.
    scenes: {
      1: [ // Project ID
        { id: 101, name: 'Dam Overflow Test', mode: 'SIL', parentId: null, config: { agents: [{id: 1, type: 'Reservoir', latLng: [47.5, -1.5], config: { initialLevel: 100 }}], connections: [] } },
        { id: 102, name: 'Pump Station Stress Test', mode: 'HIL', parentId: null, config: { agents: [], connections: [] } },
        { id: 103, name: 'Dam Overflow - High Flow Variant', mode: 'SIL', parentId: 101, config: { agents: [{id: 1, config: { initialLevel: 120 }}] } }, // Example sub-scene overriding a parameter
      ],
      2: [
        { id: 201, name: 'Canal Flow Optimization', mode: 'SIL', parentId: null, config: { agents: [], connections: [] } },
      ]
    },
  }),
  getters: {
    getScenesByProjectId: (state) => (projectId) => {
      return state.scenes[projectId] || [];
    },
    // New getter to return scenes as a tree structure for UI components
    getSceneTreeByProjectId: (state) => (projectId) => {
      const projectScenes = state.scenes[projectId] || [];
      if (!projectScenes) return [];
      return buildSceneTree(projectScenes);
    },
    // Getter to find a single scene by its ID
    getSceneById: (state) => (sceneId) => {
        for (const projectId in state.scenes) {
            const projectScenes = state.scenes[projectId];
            const scene = projectScenes.find(s => s.id === sceneId);
            if (scene) return scene;
        }
        return null;
    }
  },
  actions: {
    // The action now accepts a parentId in the sceneData
    createScene(projectId, sceneData) {
      if (!this.scenes[projectId]) {
        this.scenes[projectId] = [];
      }

      const newScene = {
        id: Date.now(),
        name: sceneData.name,
        mode: sceneData.mode,
        parentId: sceneData.parentId || null,
        config: {} // Sub-scenes start with an empty config, they inherit from their parent
      };

      this.scenes[projectId].push(newScene);
    },
    // Action to update a scene's configuration
    updateSceneConfig(sceneId, config) {
        for (const projectId in this.scenes) {
            const projectScenes = this.scenes[projectId];
            const sceneIndex = projectScenes.findIndex(s => s.id === sceneId);
            if (sceneIndex !== -1) {
                this.scenes[projectId][sceneIndex].config = config;
                return;
            }
        }
    }
  },
});
