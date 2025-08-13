import apiClient from './api';

// Note: The backend expects 'username' for login, but the frontend UI uses 'email'.
// We will need to align this. For now, we assume the payload can use email.
// The backend payload classes (LoginRequest, RegisterRequest) will be the source of truth.

export const login = async (credentials: any) => {
  try {
    const response = await apiClient.post('/auth/signin', credentials);
    if (response.data.accessToken) {
      localStorage.setItem('token', response.data.accessToken);
    }
    return response.data;
  } catch (error) {
    console.error('Login failed:', error);
    throw error;
  }
};

export const register = async (userData: any) => {
  try {
    const response = await apiClient.post('/auth/signup', userData);
    return response.data;
  } catch (error)
  {
    console.error('Registration failed:', error);
    throw error;
  }
};

export const logout = () => {
  localStorage.removeItem('token');
};
