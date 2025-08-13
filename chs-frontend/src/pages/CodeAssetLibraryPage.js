import React, { useState, useEffect } from 'react';
import { Layout, Typography, Card, Row, Col, Tag, Spin, Alert } from 'antd';
import MainLayout from '../layouts/MainLayout';
import codeAssetService from '../services/codeAssetService';

const { Title, Paragraph } = Typography;
const { Content } = Layout;

const CodeAssetLibraryPage = () => {
  const [snippets, setSnippets] = useState([]);
  const [notebooks, setNotebooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const snippetsResponse = await codeAssetService.getAllCodeSnippets();
        const notebooksResponse = await codeAssetService.getAllNotebooks();
        setSnippets(snippetsResponse.data);
        setNotebooks(notebooksResponse.data);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch code assets:", err);
        setError("无法加载代码资产，请稍后再试。");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <MainLayout>
      <Content style={{ padding: '50px' }}>
        <Title level={2}>代码片段与Notebook库</Title>
        <Paragraph>这里提供了即插即用、经过验证的代码资产，加速您的研究与开发过程。</Paragraph>

        {loading && <Spin tip="加载中..." size="large" />}
        {error && <Alert message="错误" description={error} type="error" showIcon />}

        {!loading && !error && (
          <>
            <Title level={3} style={{ marginTop: '40px' }}>代码片段</Title>
            <Row gutter={[16, 16]}>
              {snippets.map(snippet => (
                <Col span={8} key={snippet.id}>
                  <Card title={snippet.title} extra={<Tag>{snippet.language}</Tag>} hoverable>
                    {snippet.description}
                  </Card>
                </Col>
              ))}
            </Row>

            <Title level={3} style={{ marginTop: '40px' }}>交互式Notebook</Title>
            <Row gutter={[16, 16]}>
              {notebooks.map(notebook => (
                <Col span={8} key={notebook.id}>
                  <Card title={notebook.title} hoverable>
                    {notebook.description}
                  </Card>
                </Col>
              ))}
            </Row>
          </>
        )}
      </Content>
    </MainLayout>
  );
};

export default CodeAssetLibraryPage;
