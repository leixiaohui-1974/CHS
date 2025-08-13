import React, { useCallback, useEffect } from 'react';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
} from 'reactflow';
import 'reactflow/dist/style.css';
import MainLayout from '../layouts/MainLayout';
import { Layout, Typography } from 'antd';
import useKnowledgeGraphStore from '../store/useKnowledgeGraphStore';

const { Title } = Typography;
const { Content } = Layout;

const initialNodes = [
  { id: '1', position: { x: 0, y: 0 }, data: { label: '智慧水利' } },
  { id: '2', position: { x: 0, y: 100 }, data: { label: '水系统感知' } },
  { id: '3', position: { x: 200, y: 100 }, data: { label: '水系统仿真' } },
  { id: '4', position: { x: -200, y: 200 }, data: { label: '卡尔曼滤波' } },
  { id: '5', position: { x: 0, y: 200 }, data: { label: 'PID控制' } },
];

const initialEdges = [
  { id: 'e1-2', source: '1', target: '2', label: '包含' },
  { id: 'e1-3', source: '1', target: '3', label: '包含' },
  { id: 'e2-4', source: '2', target: '4', label: '应用' },
  { id: 'e3-5', source: '3', target: '5', label: '应用' },
];

const KnowledgeGraphPage = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const { highlightedNodeId, clearHighlight } = useKnowledgeGraphStore();

  useEffect(() => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === highlightedNodeId) {
          return {
            ...node,
            style: { ...node.style, backgroundColor: '#2f80ed', color: 'white' },
          };
        }
        return { ...node, style: { ...node.style, backgroundColor: undefined, color: undefined }};
      })
    );
  }, [highlightedNodeId, setNodes]);

  // Clean up highlight when leaving the page
  useEffect(() => {
    return () => {
      clearHighlight();
    };
  }, [clearHighlight]);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  return (
    <MainLayout>
      <Content style={{ padding: '0', height: 'calc(100vh - 112px)' }}>
        <Title level={2} style={{ padding: '24px' }}>知识图谱浏览器</Title>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          fitView
        >
          <Controls />
          <MiniMap />
          <Background variant="dots" gap={12} size={1} />
        </ReactFlow>
      </Content>
    </MainLayout>
  );
};

export default KnowledgeGraphPage;
