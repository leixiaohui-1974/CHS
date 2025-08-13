import apiClient from './api';

export interface Project {
  id: number;
  name: string;
  description: string;
  // Add other project properties as defined by the backend
}

export const getProjects = async (): Promise<Project[]> => {
  const response = await apiClient.get('/projects');
  return response.data;
};

export const getProjectById = async (id: number): Promise<Project> => {
  const response = await apiClient.get(`/projects/${id}`);
  return response.data;
};

export const createProject = async (projectData: { name: string; description: string }): Promise<Project> => {
  const response = await apiClient.post('/projects', projectData);
  return response.data;
};

export const updateProject = async (id: number, projectData: { name: string; description: string }): Promise<Project> => {
  const response = await apiClient.put(`/projects/${id}`, projectData);
  return response.data;
};

export const deleteProject = async (id: number): Promise<void> => {
  await apiClient.delete(`/projects/${id}`);
};
