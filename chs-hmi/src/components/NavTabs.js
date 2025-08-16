import React from 'react';

const NavTabs = ({ activeView, onSelectView }) => {
  const tabStyle = {
    padding: '10px 20px',
    cursor: 'pointer',
    borderBottom: '2px solid transparent',
    display: 'inline-block',
  };

  const activeTabStyle = {
    ...tabStyle,
    color: '#007bff',
    borderBottom: '2px solid #007bff',
  };

  const navContainerStyle = {
    textAlign: 'center',
    marginBottom: '20px',
    borderBottom: '1px solid #ddd',
  };

  return (
    <div style={navContainerStyle}>
      <div
        style={activeView === 'dashboard' ? activeTabStyle : tabStyle}
        onClick={() => onSelectView('dashboard')}
      >
        监控仪表盘
      </div>
      <div
        style={activeView === 'topology' ? activeTabStyle : tabStyle}
        onClick={() => onSelectView('topology')}
      >
        系统拓扑
      </div>
      <div
        style={activeView === 'settings' ? activeTabStyle : tabStyle}
        onClick={() => onSelectView('settings')}
      >
        远程配置
      </div>
    </div>
  );
};

export default NavTabs;
