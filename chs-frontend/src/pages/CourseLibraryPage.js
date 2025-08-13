import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Layout, Typography, Card, Row, Col, Spin, Alert } from 'antd';
import MainLayout from '../layouts/MainLayout';
import courseService from '../services/courseService';

const { Title } = Typography;
const { Content } = Layout;

const CourseLibraryPage = () => {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    courseService.getAllCourses()
      .then(response => {
        setCourses(response.data);
        setLoading(false);
      })
      .catch(error => {
        console.error("Failed to fetch courses:", error);
        setError("无法加载课程列表，请稍后再试。");
        setLoading(false);
      });
  }, []);

  return (
    <MainLayout>
      <Content style={{ padding: '50px' }}>
        <Title level={2}>精品课程库</Title>
        <p>在这里，您可以系统性地学习智慧水务领域的专业知识，从理论基础到项目实践。</p>

        {loading && <Spin tip="加载中..." size="large" />}
        {error && <Alert message="错误" description={error} type="error" showIcon />}

        {!loading && !error && (
          <Row gutter={[16, 16]} style={{ marginTop: '24px' }}>
            {courses.map(course => (
              <Col span={8} key={course.id}>
                <Link to={`/courses/${course.id}`}>
                  <Card title={course.title} hoverable>
                    {course.description}
                  </Card>
                </Link>
              </Col>
            ))}
          </Row>
        )}
      </Content>
    </MainLayout>
  );
};

export default CourseLibraryPage;
