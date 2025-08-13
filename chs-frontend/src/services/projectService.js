import axios from 'axios';
import authHeader from './authService';

const API_URL = '/api/projects/'; // Replace with your actual backend API URL

// Mock data until backend is ready
let mockProjects = [
  { id: 1, name: 'Project Alpha', description: 'Digital twin for the main water channel.', createdAt: new Date().toISOString() },
  { id: 2, name: 'Project Beta', description: 'Reservoir simulation model.', createdAt: new Date().toISOString() },
  { id: 3, name: 'Project Gamma', description: 'Urban drainage system analysis.', createdAt: new Date().toISOString() },
];
let nextId = 4;

const getProjects = () => {
  // Real implementation:
  // return axios.get(API_URL, { headers: authHeader() });
  return new Promise(resolve => {
    setTimeout(() => resolve({ data: mockProjects }), 500);
  });
};

const createProject = (project) => {
  // Real implementation:
  // return axios.post(API_URL, project, { headers: authHeader() });
  return new Promise(resolve => {
    const newProject = { ...project, id: nextId++, createdAt: new Date().toISOString() };
    mockProjects.push(newProject);
    setTimeout(() => resolve({ data: newProject }), 500);
  });
};

const updateProject = (id, project) => {
  // Real implementation:
  // return axios.put(API_URL + id, project, { headers: authHeader() });
   return new Promise(resolve => {
    mockProjects = mockProjects.map(p => (p.id === id ? { ...p, ...project } : p));
    setTimeout(() => resolve({ data: mockProjects.find(p => p.id === id) }), 500);
  });
};

const deleteProject = (id) => {
  // Real implementation:
  // return axios.delete(API_URL + id, { headers: authHeader() });
  return new Promise(resolve => {
    mockProjects = mockProjects.filter(p => p.id !== id);
    setTimeout(() => resolve({ data: { message: 'Project deleted' } }), 500);
  });
};


const projectService = {
  getProjects,
  createProject,
  updateProject,
  deleteProject,
};

export default projectService;
