import axios from 'axios';
import authHeader from './authService';

const API_URL = '/api/projects/'; // Replace with your actual backend API URL

const getProjects = () => {
  return axios.get(API_URL, { headers: authHeader() });
};

const createProject = (project) => {
  return axios.post(API_URL, project, { headers: authHeader() });
};

const updateProject = (id, project) => {
  return axios.put(API_URL + id, project, { headers: authHeader() });
};

const deleteProject = (id) => {
  return axios.delete(API_URL + id, { headers: authHeader() });
};


const projectService = {
  getProjects,
  createProject,
  updateProject,
  deleteProject,
};

export default projectService;
