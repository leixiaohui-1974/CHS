import React, { useState } from 'react';
import { Layout, Menu, Button, Avatar, Dropdown, Space } from 'antd';
import {
  MenuUnfoldOutlined,
  MenuFoldOutlined,
  DashboardOutlined,
  ProjectOutlined,
  UserOutlined,
  DownOutlined,
  ReadOutlined, // Icon for Courses
  CodeOutlined, // Icon for Code Assets
  ApartmentOutlined, // Icon for Knowledge Graph
} from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import useAuthStore from '../store/useAuthStore';

const { Header, Sider, Content } = Layout;

const MainLayout = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const userMenu = (
    <Menu>
      <Menu.Item key="1">Profile</Menu.Item>
      <Menu.Item key="2" onClick={handleLogout}>
        Logout
      </Menu.Item>
    </Menu>
  );

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider trigger={null} collapsible collapsed={collapsed}>
        <div className="logo" style={{ height: '32px', margin: '16px', background: 'rgba(255, 255, 255, 0.3)', color: 'white', textAlign: 'center', lineHeight: '32px' }}>
          {collapsed ? 'CHS' : 'CHS Platform'}
        </div>
        <Menu theme="dark" mode="inline" defaultSelectedKeys={['1']}>
          <Menu.Item key="1" icon={<DashboardOutlined />}>
            <Link to="/dashboard">Dashboard</Link>
          </Menu.Item>
          <Menu.Item key="2" icon={<ProjectOutlined />}>
            <Link to="/workbench">Modeling Workbench</Link>
          </Menu.Item>
          <Menu.Item key="3" icon={<ApartmentOutlined />}>
            <Link to="/knowledge-graph">知识图谱</Link>
          </Menu.Item>
          <Menu.Item key="4" icon={<ReadOutlined />}>
            <Link to="/courses">精品课程</Link>
          </Menu.Item>
          <Menu.Item key="5" icon={<CodeOutlined />}>
            <Link to="/assets">代码库</Link>
          </Menu.Item>
        </Menu>
      </Sider>
      <Layout className="site-layout">
        <Header className="site-layout-background" style={{ padding: '0 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          {React.createElement(collapsed ? MenuUnfoldOutlined : MenuFoldOutlined, {
            className: 'trigger',
            onClick: () => setCollapsed(!collapsed),
            style: { color: '#fff' }
          })}
          <Dropdown overlay={userMenu}>
            <a onClick={e => e.preventDefault()} style={{color: '#fff'}}>
              <Space>
                <Avatar icon={<UserOutlined />} />
                {user?.username}
                <DownOutlined />
              </Space>
            </a>
          </Dropdown>
        </Header>
        <Content
          className="site-layout-background"
          style={{
            margin: '24px 16px',
            padding: 24,
            minHeight: 280,
          }}
        >
          {children}
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
