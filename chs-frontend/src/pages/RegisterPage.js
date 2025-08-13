import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, Alert } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import authService from '../services/authService';

const { Title } = Typography;

const RegisterPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const onFinish = (values) => {
    setLoading(true);
    setError('');
    setSuccess(false);
    authService.register(values.username, values.password).then(
      (response) => {
        setSuccess(true);
        setLoading(false);
        // navigate('/login'); // Optionally navigate to login after a delay
      },
      (err) => {
        const resMessage =
          (err.response &&
            err.response.data &&
            err.response.data.message) ||
          err.message ||
          err.toString();
        setError(resMessage);
        setLoading(false);
      }
    );
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f0f2f5' }}>
      <Card style={{ width: 400 }}>
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <Title level={2}>Create Account</Title>
        </div>
        <Form
          name="register"
          onFinish={onFinish}
          scrollToFirstError
        >
          {error && <Alert message={error} type="error" showIcon style={{ marginBottom: 24 }} />}
          {success && <Alert message="Registration successful! You can now log in." type="success" showIcon style={{ marginBottom: 24 }} />}
          <Form.Item
            name="username"
            rules={[{ required: true, message: 'Please input your Username!', whitespace: true }]}
          >
            <Input prefix={<UserOutlined />} placeholder="Username" />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: 'Please input your password!' }]}
            hasFeedback
          >
            <Input.Password prefix={<LockOutlined />} placeholder="Password" />
          </Form.Item>

          <Form.Item
            name="confirm"
            dependencies={['password']}
            hasFeedback
            rules={[
              { required: true, message: 'Please confirm your password!' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('The two passwords that you entered do not match!'));
                },
              }),
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="Confirm Password" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" style={{ width: '100%' }} loading={loading}>
              Register
            </Button>
            Already have an account? <Link to="/login">Log in</Link>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default RegisterPage;
