import axios from 'axios';

/**
 * Fetches the system status from the backend API.
 * The proxy in package.json will forward this request to the backend.
 * @returns {Promise<Object>} A promise that resolves to the system status data.
 */
export const fetchSystemStatus = async () => {
  try {
    // Using a relative path because of the "proxy" setting in package.json
    const response = await axios.get('/api/v1/system_status');
    return response.data;
  } catch (error) {
    // Log the error and re-throw it to be handled by the calling component
    console.error('Error fetching system status:', error);
    // It's good practice to inform the user about the error.
    // We can throw a more specific error message.
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      throw new Error(`Backend error: ${error.response.status} ${error.response.data.message || ''}`);
    } else if (error.request) {
      // The request was made but no response was received
      throw new Error('Could not connect to the server. Please check if the backend is running.');
    } else {
      // Something happened in setting up the request that triggered an Error
      throw new Error(`An unexpected error occurred: ${error.message}`);
    }
  }
};
