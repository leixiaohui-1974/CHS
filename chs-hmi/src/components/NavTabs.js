import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';

const NavTabs = ({ activeView, onSelectView }) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleNav = (view) => {
    if (view === 'reporting') {
      navigate('/reporting');
    } else {
      if (location.pathname !== '/') {
        navigate('/');
      }
      onSelectView(view);
    }
  };

  const getStyle = (path, view = null) => {
    let isActive = location.pathname === path;
    if (path === '/' && view) {
        isActive = location.pathname === '/' && activeView === view;
    }

    const baseStyle = {
      padding: '10px 20px',
      cursor: 'pointer',
      borderBottom: '2px solid transparent',
      display: 'inline-block',
      textDecoration: 'none',
      color: 'inherit',
      margin: '0 10px',
    };

    if (isActive) {
      return {
        ...baseStyle,
        color: '#007bff',
        borderBottom: '2px solid #007bff',
        fontWeight: 'bold',
      };
    }
    return baseStyle;
  };

  const navContainerStyle = {
    textAlign: 'center',
    marginBottom: '20px',
    borderBottom: '1px solid #ddd',
    paddingBottom: '10px',
  };

  return (
    <div style={navContainerStyle}>
      <div style={getStyle('/', 'dashboard')} onClick={() => handleNav('dashboard')}>
        监控仪表盘
      </div>
      <div style={getStyle('/reporting', null)} onClick={() => handleNav('reporting')}>
        报告中心
      </div>

      {location.pathname === '/' && (
        <>
          <div
            style={getStyle('/', 'topology')}
            onClick={() => handleNav('topology')}
          >
            系统拓扑
          </div>
          {user && user.role === 'admin' && (
            <div
              style={getStyle('/', 'settings')}
              onClick={() => handleNav('settings')}
            >
              远程配置
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default NavTabs;
