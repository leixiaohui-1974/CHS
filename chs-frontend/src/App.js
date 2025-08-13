import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import WorkbenchPage from './pages/WorkbenchPage';
import SituationalAwarenessPage from './pages/SituationalAwarenessPage';
import CourseLibraryPage from './pages/CourseLibraryPage';
import CodeAssetLibraryPage from './pages/CodeAssetLibraryPage';
import CourseDetailPage from './pages/CourseDetailPage';
import KnowledgeGraphPage from './pages/KnowledgeGraphPage'; // Import graph page
import MainLayout from './layouts/MainLayout';
import authService from './services/authService';

const App = () => {
  const currentUser = authService.getCurrentUser();

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/*"
          element={
            currentUser ? (
              <MainLayout>
                <Routes>
                  <Route path="/" element={<SituationalAwarenessPage />} />
                  <Route path="/dashboard" element={<DashboardPage />} />
                  <Route path="/workbench" element={<WorkbenchPage />} />
                  <Route path="/courses" element={<CourseLibraryPage />} />
                  <Route path="/courses/:id" element={<CourseDetailPage />} />
                  <Route path="/assets" element={<CodeAssetLibraryPage />} />
                  <Route path="/knowledge-graph" element={<KnowledgeGraphPage />} />
                  {/* Other protected routes can go here */}
                  <Route path="*" element={<Navigate to="/" />} />
                </Routes>
              </MainLayout>
            ) : (
              <Navigate to="/login" />
            )
          }
        />
      </Routes>
    </Router>
  );
};

export default App;
