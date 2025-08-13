import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Layout, Typography, Spin, Alert, List, Card, Breadcrumb } from 'antd';
import MainLayout from '../layouts/MainLayout';
import courseService from '../services/courseService';
import useKnowledgeGraphStore from '../store/useKnowledgeGraphStore';

const { Title, Paragraph } = Typography;
const { Content } = Layout;

const CourseDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { setHighlightedNodeId } = useKnowledgeGraphStore();
  const [course, setCourse] = useState(null);
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const contentRef = useRef(null);

  useEffect(() => {
    const fetchCourseData = async () => {
      try {
        setLoading(true);
        const courseResponse = await courseService.getCourseById(id);
        // For demo, let's assume lesson content has special links
        // e.g., <a href="#" data-knowledge-point="4">卡尔曼滤波</a>
        const lessonsResponse = await courseService.getLessonsByCourseId(id);
        setCourse(courseResponse.data);
        setLessons(lessonsResponse.data);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch course details:", err);
        setError("无法加载课程详情，请稍后再试。");
      } finally {
        setLoading(false);
      }
    };
    fetchCourseData();
  }, [id]);

  useEffect(() => {
    const handleKnowledgeLinkClick = (e) => {
      const target = e.target.closest('a[data-knowledge-point]');
      if (!target) return;

      e.preventDefault();
      const nodeId = target.getAttribute('data-knowledge-point');
      console.log('Highlighting node:', nodeId);
      setHighlightedNodeId(nodeId);
      navigate('/knowledge-graph');
    };

    const contentElement = contentRef.current;
    if (contentElement) {
      contentElement.addEventListener('click', handleKnowledgeLinkClick);
    }

    return () => {
      if (contentElement) {
        contentElement.removeEventListener('click', handleKnowledgeLinkClick);
      }
    };
  }, [lessons, navigate, setHighlightedNodeId]);

  if (loading) {
    return <MainLayout><Spin tip="加载中..." size="large" style={{ display: 'block', marginTop: '50px' }} /></MainLayout>;
  }

  if (error) {
    return <MainLayout><Alert message="错误" description={error} type="error" showIcon /></MainLayout>;
  }

  return (
    <MainLayout>
      <Content style={{ padding: '50px' }}>
        <Breadcrumb style={{ marginBottom: '16px' }}>
          <Breadcrumb.Item><Link to="/courses">精品课程库</Link></Breadcrumb.Item>
          <Breadcrumb.Item>{course?.title}</Breadcrumb.Item>
        </Breadcrumb>

        <Card>
          <Title level={2}>{course?.title}</Title>
          <Paragraph>{course?.description}</Paragraph>
        </Card>

        <Title level={3} style={{ marginTop: '40px' }}>课程章节</Title>
        <div ref={contentRef}>
          <List
            grid={{ gutter: 16, column: 1 }}
            dataSource={lessons}
            renderItem={lesson => (
              <List.Item>
                <Card title={`第 ${lesson.lessonOrder} 章: ${lesson.title}`}>
                  <div dangerouslySetInnerHTML={{ __html: lesson.content }} />
                </Card>
              </List.Item>
            )}
          />
        </div>
      </Content>
    </MainLayout>
  );
};

export default CourseDetailPage;
