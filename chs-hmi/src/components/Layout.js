import React, { useState, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import NavTabs from './NavTabs';

const Layout = ({ children }) => {
  const [activeView, setActiveView] = useState('dashboard');
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const dashboardRef = useRef();

  const [isEditMode, setIsEditMode] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleSaveLayout = () => {
    if (dashboardRef.current && typeof dashboardRef.current.saveLayout === 'function') {
      dashboardRef.current.saveLayout();
    }
    setIsEditMode(false);
  };

  const headerStyle = {
    width: '100%',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '10px 20px',
    boxSizing: 'border-box',
    borderBottom: '1px solid #eee',
    backgroundColor: '#fff',
  };

  const userInfoStyle = {
    fontSize: '14px',
    color: '#666',
  };

  const buttonGroupStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  };

  const baseButtonStyle = {
    padding: '8px 16px',
    fontSize: '14px',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  };

  const editButtonStyle = {
    ...baseButtonStyle,
    color: '#fff',
    backgroundColor: '#007bff',
  };

  const saveButtonStyle = {
    ...baseButtonStyle,
    color: '#fff',
    backgroundColor: '#28a745',
  };

  const logoutButtonStyle = {
    ...baseButtonStyle,
    color: '#fff',
    backgroundColor: '#dc3545',
  };

  const mainContentStyle = {
    padding: '20px',
  };

  const isDashboardPage = location.pathname === '/';

  const childrenWithProps = React.cloneElement(children, {
      ref: isDashboardPage ? dashboardRef : null,
      isEditMode: isDashboardPage ? isEditMode : false,
      activeView: activeView,
      setActiveView: setActiveView,
  });


  return (
    <div>
      <header style={headerStyle}>
        <h1>CHS 智慧运营门户</h1>
        {user && (
          <div style={buttonGroupStyle}>
            <span style={userInfoStyle}>欢迎, {user.name} ({user.role})</span>
            {isDashboardPage && (
              <>
                <button onClick={() => setIsEditMode(!isEditMode)} style={editButtonStyle}>
                  {isEditMode ? '取消编辑' : '编辑布局'}
                </button>
                {isEditMode && (
                  <button onClick={handleSaveLayout} style={saveButtonStyle}>
                    保存布局
                  </button>
                )}
              </>
            )}
            <button onClick={handleLogout} style={logoutButtonStyle}>
              登出
            </button>
          </div>
        )}
      </header>

      <NavTabs activeView={activeView} onSelectView={setActiveView} />

      <main style={mainContentStyle}>
        {childrenWithProps}
      </main>
    </div>
  );
};

export default Layout;
