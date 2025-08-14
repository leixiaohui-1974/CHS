import { defineStore } from 'pinia';

export const useProjectStore = defineStore('project', {
  state: () => ({
    projects: [
      { id: 1, name: 'Project Alpha', description: 'SIL simulation for a water dam.' },
      { id: 2, name: 'Project Beta', description: 'HIL testing for a pump station.' },
    ],
  }),
  actions: {
    async createProject(project) {
      // In a real app, this would be an API call
      const newProject = { ...project, id: Date.now() };
      this.projects.push(newProject);
    },
  },
});
