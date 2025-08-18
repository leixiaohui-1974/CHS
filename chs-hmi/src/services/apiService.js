import axios from 'axios';
import { mockEvents, mockSystemTopology } from '../mockData.js';

// =================== AUTH ===================
export const setAuthToken = (token) => {
  if (token) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete axios.defaults.headers.common['Authorization'];
  }
};

export const login = async (username, password) => {
  // This is a mock login function.
  // In a real application, this would make a request to a server.
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if ((username === 'admin' && password === 'admin') ||
          (username === 'manager' && password === 'manager') ||
          (username === 'operator' && password === 'operator')) {
        resolve({ token: `fake-jwt-token-for-${username}` });
      } else {
        reject(new Error('用户名或密码无效。'));
      }
    }, 500);
  });
};

export const fetchCurrentUser = async () => {
    // This is a mock user fetch function.
    const username = localStorage.getItem('username');
    return new Promise((resolve, reject) => {
        const mockUser = {
            'admin': { id: 1, name: 'Admin User', role: 'admin' },
            'manager': { id: 2, name: 'Manager User', role: 'manager' },
            'operator': { id: 3, name: 'Operator User', role: 'operator' }
        }[username];

        if (mockUser) {
            resolve(mockUser);
        } else {
            // This case handles when the app loads but there's no user in local storage
            // It shouldn't be treated as an error, but as an unauthenticated state.
            resolve(null);
        }
    });
};


// =================== DASHBOARDS ===================
export const fetchDashboardLayouts = async () => {
  try {
    // In a real app, this would fetch from a user-specific endpoint.
    // For this mock, we'll use localStorage.
    const layouts = localStorage.getItem('dashboardLayouts');
    return layouts ? JSON.parse(layouts) : null;
  } catch (error) {
    console.error('Error fetching dashboard layouts from localStorage', error);
    return null;
  }
};

export const saveDashboardLayout = async (layouts) => {
   try {
    // In a real app, this would be a POST request.
    // For this mock, we'll use localStorage.
    localStorage.setItem('dashboardLayouts', JSON.stringify({ layouts }));
    return { success: true };
  } catch (error) {
    console.error('Error saving dashboard layout to localStorage', error);
    throw new Error('Failed to save layout.');
  }
};


// =================== REPORTS ===================
export const generateReport = async (reportType, dateRange) => {
  console.log(`Generating report request: ${reportType} for ${dateRange}`);
  // Mocking the API call
  return Promise.resolve({ task_id: `task-${Math.random().toString(36).substr(2, 9)}` });
};

export const fetchReportStatus = async (taskId) => {
  console.log(`Polling for task ${taskId}...`);
  // This is a mock.
  return new Promise((resolve) => {
    setTimeout(() => {
      // Use a static variable to track poll count for simplicity
      if (!window.pollCount) window.pollCount = 0;
      window.pollCount++;

      if (window.pollCount < 2) {
        resolve({ task_id: taskId, status: 'PENDING' });
      } else {
        window.pollCount = 0; // Reset for next time
        resolve({
          task_id: taskId,
          status: 'SUCCESS',
          download_url: `/reports/mock-report-${taskId}.pdf`,
        });
      }
    }, 2000);
  });
};


// =================== ORIGINAL/EXISTING FUNCTIONS ===================
export const fetchSystemStatus = async () => {
  try {
    // Using a relative path because of the "proxy" setting in package.json
    // const response = await axios.get('/api/v1/system_status');
    // return response.data;
    // Mocking system status to avoid network errors during testing
    return Promise.resolve({
        "device-001": { "name": "核心交换机-A", "status": "normal", "ip_address": "192.168.1.1", "uptime": "365d 4h 12m" },
        "device-002": { "name": "汇聚交换机-B", "status": "warning", "ip_address": "192.168.1.2", "cpu_load": 85 },
        "device-003": { "name": "接入服务器-C", "status": "critical", "ip_address": "10.0.0.5", "disk_usage": "95%" },
        "device-004": { "name": "数据库服务器", "status": "normal", "ip_address": "10.0.0.6", "ram_usage": "60%" }
    });
  } catch (error) {
    console.error('Error fetching system status:', error);
    if (error.response) {
      throw new Error(`Backend error: ${error.response.status} ${error.response.data.message || ''}`);
    } else if (error.request) {
      throw new Error('Could not connect to the server. Please check if the backend is running.');
    } else {
      throw new Error(`An unexpected error occurred: ${error.message}`);
    }
  }
};

export const fetchDeviceHistory = async (deviceId, range) => {
  try {
    const response = await axios.get(`/api/v1/devices/${deviceId}/history`, {
      params: { range },
    });
    return response.data;
  } catch (error) {
    console.error(`Error fetching history for device ${deviceId}:`, error);
    if (error.response) {
      throw new Error(`Backend error: ${error.response.status} ${error.response.data.message || ''}`);
    } else if (error.request) {
      throw new Error('Could not connect to the server.');
    } else {
      throw new Error(`An unexpected error occurred: ${error.message}`);
    }
  }
};

export const fetchEvents = async () => {
  try {
    // const response = await axios.get('/api/v1/events');
    // return response.data;
    console.log("Using mock data for events.");
    return Promise.resolve(mockEvents);
  } catch (error) {
    console.error('Error fetching events:', error);
    if (error.response) {
      throw new Error(`Backend error: ${error.response.status} ${error.response.data.message || ''}`);
    } else if (error.request) {
      throw new Error('Could not connect to the server.');
    } else {
      throw new Error(`An unexpected error occurred: ${error.message}`);
    }
  }
};

export const acknowledgeEvent = async (eventId) => {
  console.log(`Acknowledging event ${eventId}...`);
  // In a real app, this would be:
  // await axios.post(`/api/v1/events/${eventId}/ack`);
  return Promise.resolve({ success: true, message: `Event ${eventId} acknowledged.` });
};

export const resolveEvent = async (eventId, notes) => {
  console.log(`Resolving event ${eventId} with notes: "${notes}"`);
  // In a real app, this would be:
  // await axios.post(`/api/v1/events/${eventId}/resolve`, { notes });
  return Promise.resolve({ success: true, message: `Event ${eventId} resolved.` });
};

export const getSystemTopology = async (projectId) => {
  if (!projectId) {
    console.error("getSystemTopology requires a projectId.");
    // Return a default or empty topology to prevent UI crashes
    return { components: {}, connections: [] };
  }
  try {
    // Note: The backend uses /api/projects/{projectId}/topology
    // The '/api' prefix is handled by the proxy in package.json
    const response = await axios.get(`/api/projects/${projectId}/topology`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching system topology for project ${projectId}:`, error);
    if (error.response) {
      throw new Error(`Backend error: ${error.response.status} ${error.response.data.message || ''}`);
    } else if (error.request) {
      throw new Error('Could not connect to the server.');
    } else {
      throw new Error(`An unexpected error occurred: ${error.message}`);
    }
  }
};

export const updateDeviceConfig = async (deviceId, config) => {
  console.log(`Updating config for device ${deviceId}:`, config);
  // In a real app, this would be:
  // await axios.post(`/api/v1/devices/${deviceId}/config`, config);
  return Promise.resolve({ success: true, message: `Device ${deviceId} configuration updated.` });
};

/**
 * Starts a training job for a project.
 * @param {string} projectId - The ID of the project.
 * @param {object} params - The training parameters (e.g., { algorithm: 'PPO', total_timesteps: 100000 }).
 * @returns {Promise<Object>} A promise that resolves to the new model data.
 */
export const trainAgent = async (projectId, params) => {
  try {
    const response = await axios.post(`/api/projects/${projectId}/train`, params);
    return response.data;
  } catch (error) {
    console.error(`Error starting training for project ${projectId}:`, error);
    if (error.response) {
      throw new Error(`Backend error: ${error.response.status} ${error.response.data.message || ''}`);
    } else if (error.request) {
      throw new Error('Could not connect to the server.');
    } else {
      throw new Error(`An unexpected error occurred: ${error.message}`);
    }
  }
};

/**
 * Fetches the list of trained models for a project.
 * @param {string} projectId - The ID of the project.
 * @returns {Promise<Array>} A promise that resolves to an array of model objects.
 */
export const fetchProjectModels = async (projectId) => {
  try {
    const response = await axios.get(`/api/projects/${projectId}/models`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching models for project ${projectId}:`, error);
    if (error.response) {
      throw new Error(`Backend error: ${error.response.status} ${error.response.data.message || ''}`);
    } else if (error.request) {
      throw new Error('Could not connect to the server.');
    } else {
      throw new Error(`An unexpected error occurred: ${error.message}`);
    }
  }
};
