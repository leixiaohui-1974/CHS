import React, { createContext, useState, useEffect, useContext } from 'react';
import { fetchCurrentUser, setAuthToken } from '../services/apiService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadUser = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        setAuthToken(token);
        try {
          const currentUser = await fetchCurrentUser();
          setUser(currentUser);
        } catch (error) {
          console.error("Failed to load user. Token might be invalid.", error);
          localStorage.removeItem('token');
          localStorage.removeItem('username');
          setAuthToken(null);
        }
      }
      setIsLoading(false);
    };

    loadUser();
  }, []);

  const login = async (username, password) => {
    // In a real app, this would use the apiService.login
    // For this mock, we simulate it.
    return new Promise((resolve, reject) => {
        setTimeout(() => {
          if ((username === 'admin' && password === 'admin') ||
              (username === 'manager' && password === 'manager') ||
              (username === 'operator' && password === 'operator')) {
            const mockToken = `fake-jwt-token-for-${username}`;
            localStorage.setItem('token', mockToken);
            localStorage.setItem('username', username); // Store username for mock role
            setAuthToken(mockToken);

            const mockUser = {
              'admin': { id: 1, name: 'Admin User', role: 'admin' },
              'manager': { id: 2, name: 'Manager User', role: 'manager' },
              'operator': { id: 3, name: 'Operator User', role: 'operator' }
            }[username];

            setUser(mockUser);
            resolve(mockUser);
          } else {
            reject(new Error('用户名或密码无效。'));
          }
        }, 500);
      });
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    setAuthToken(null);
    setUser(null);
  };

  const value = {
    user,
    setUser,
    isLoading,
    login,
    logout,
  };

  // Render children only when not loading initial user data
  return (
    <AuthContext.Provider value={value}>
      {!isLoading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
