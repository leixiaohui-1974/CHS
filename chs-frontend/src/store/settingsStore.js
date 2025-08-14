import { defineStore } from 'pinia';

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    interventionLevel: 'full_autonomy', // Default level
  }),
  actions: {
    setInterventionLevel(level) {
      this.interventionLevel = level;
    },
  },
});
