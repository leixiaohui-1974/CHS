import { defineStore } from 'pinia';
import { ref } from 'vue';
import {
  getProjects,
  createProject,
  updateProject,
  deleteProject,
  type Project,
} from '@/services/projectService';
import { message } from 'ant-design-vue';

export const useProjectStore = defineStore('projects', () => {
  const projects = ref<Project[]>([]);
  const isLoading = ref(false);

  async function fetchProjects() {
    isLoading.value = true;
    try {
      projects.value = await getProjects();
    } catch (error) {
      message.error('Failed to fetch projects.');
      projects.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  async function addProject(projectData: { name: string; description: string }) {
    isLoading.value = true;
    try {
      const newProject = await createProject(projectData);
      projects.value.push(newProject);
      message.success('Project created successfully!');
    } catch (error) {
      message.error('Failed to create project.');
    } finally {
      isLoading.value = false;
    }
  }

  async function editProject(id: number, projectData: { name: string; description: string }) {
    isLoading.value = true;
    try {
      const updatedProject = await updateProject(id, projectData);
      const index = projects.value.findIndex((p) => p.id === id);
      if (index !== -1) {
        projects.value[index] = updatedProject;
      }
      message.success('Project updated successfully!');
    } catch (error) {
      message.error('Failed to update project.');
    } finally {
      isLoading.value = false;
    }
  }

  async function removeProject(id: number) {
    isLoading.value = true;
    try {
      await deleteProject(id);
      projects.value = projects.value.filter((p) => p.id !== id);
      message.success('Project deleted successfully!');
    } catch (error) {
      message.error('Failed to delete project.');
    } finally {
      isLoading.value = false;
    }
  }

  return { projects, isLoading, fetchProjects, addProject, editProject, removeProject };
});
