import React, { useState, useEffect } from 'react';
import { Table, Button, Popconfirm, message, Space, Modal, Form, Input, Typography } from 'antd';
import projectService from '../services/projectService';

const { TextArea } = Input;
const { Title } = Typography;

const ProjectForm = ({ visible, onCancel, onCreate, onUpdate, initialData }) => {
  const [form] = Form.useForm();

  useEffect(() => {
    if (initialData) {
      form.setFieldsValue(initialData);
    } else {
      form.resetFields();
    }
  }, [initialData, form]);

  return (
    <Modal
      visible={visible}
      title={initialData ? 'Edit Project' : 'Create a new project'}
      okText={initialData ? 'Update' : 'Create'}
      cancelText="Cancel"
      onCancel={onCancel}
      onOk={() => {
        form
          .validateFields()
          .then((values) => {
            form.resetFields();
            if (initialData) {
              onUpdate(initialData.id, values);
            } else {
              onCreate(values);
            }
          })
          .catch((info) => {
            console.log('Validate Failed:', info);
          });
      }}
    >
      <Form form={form} layout="vertical" name="form_in_modal">
        <Form.Item
          name="name"
          label="Project Name"
          rules={[{ required: true, message: 'Please input the name of the project!' }]}
        >
          <Input />
        </Form.Item>
        <Form.Item name="description" label="Description">
          <TextArea rows={4} />
        </Form.Item>
      </Form>
    </Modal>
  );
};


const DashboardPage = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingProject, setEditingProject] = useState(null);

  const fetchProjects = () => {
    setLoading(true);
    projectService.getProjects().then(
      (response) => {
        setProjects(response.data);
        setLoading(false);
      },
      (error) => {
        console.error('Error fetching projects', error);
        message.error('Could not fetch projects.');
        setLoading(false);
      }
    );
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleCreate = (values) => {
    projectService.createProject(values).then(() => {
      message.success('Project created successfully.');
      setModalVisible(false);
      fetchProjects();
    });
  };

  const handleUpdate = (id, values) => {
    projectService.updateProject(id, values).then(() => {
      message.success('Project updated successfully.');
      setModalVisible(false);
      setEditingProject(null);
      fetchProjects();
    });
  };

  const handleDelete = (id) => {
    projectService.deleteProject(id).then(() => {
      message.success('Project deleted successfully.');
      fetchProjects(); // Refresh the list
    });
  };

  const handleEdit = (project) => {
    setEditingProject(project);
    setModalVisible(true);
  };

  const columns = [
    {
      title: 'Project Name',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: 'Creation Date',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: (text) => new Date(text).toLocaleDateString(),
    },
    {
      title: 'Action',
      key: 'action',
      render: (text, record) => (
        <Space size="middle">
          <Button type="primary" onClick={() => handleEdit(record)}>Edit</Button>
          <Popconfirm
            title="Are you sure you want to delete this project?"
            onConfirm={() => handleDelete(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Button type="primary" danger>Delete</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <Title level={2}>Projects Dashboard</Title>
        <Button type="primary" onClick={() => setModalVisible(true)}>
          Create Project
        </Button>
      </div>
      <ProjectForm
        visible={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setEditingProject(null);
        }}
        onCreate={handleCreate}
        onUpdate={handleUpdate}
        initialData={editingProject}
      />
      <Table
        columns={columns}
        dataSource={projects}
        rowKey="id"
        loading={loading}
        style={{ marginTop: 20 }}
      />
    </div>
  );
};

export default DashboardPage;
