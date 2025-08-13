import React, { useRef, useCallback } from 'react';
import { Layout, Tree, Divider, Typography, Button } from 'antd';
import ReactFlow, {
  ReactFlowProvider,
  Controls,
  Background,
  useReactFlow,
} from 'reactflow';
import useWorkflowStore from '../store/useWorkflowStore';
import 'reactflow/dist/style.css';
import './WorkbenchPage.css';

const { Sider, Content } = Layout;
const { Title } = Typography;

let id = 0;
const getId = () => `dndnode_${id++}`;

const ComponentPalette = () => {
  const onDragStart = (event, nodeType, label) => {
    event.dataTransfer.setData('application/reactflow-type', nodeType);
    event.dataTransfer.setData('application/reactflow-label', label);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div className="component-palette">
        <Title level={4}>Component Palette</Title>
        <div className="draggable-node" onDragStart={(event) => onDragStart(event, 'default', 'Reservoir')} draggable>
          Reservoir
        </div>
        <div className="draggable-node" onDragStart={(event) => onDragStart(event, 'default', 'Channel')} draggable>
          Channel
        </div>
        <div className="draggable-node" onDragStart={(event) => onDragStart(event, 'output', 'Outlet')} draggable>
          Outlet
        </div>
    </div>
  );
}

const SceneManager = () => {
    const nodes = useWorkflowStore((state) => state.nodes);
    const components = useWorkflowStore((state) => state.components);
    const connections = useWorkflowStore((state) => state.connections);

    const treeData = [
        {
          title: 'Scene Root',
          key: '0-0',
          children: nodes.map(node => ({ title: node.data.label, key: node.id })),
        },
    ];

    const onSave = () => {
        const workflowData = {
            components: components,
            connections: connections,
        };
        console.log('Workflow Saved:', JSON.stringify(workflowData, null, 2));
        // Here you would typically send this JSON to a backend API
    };

    return (
        <div>
            <Title level={4}>Scene Manager</Title>
            <Tree
              showLine
              defaultExpandedKeys={['0-0']}
              treeData={treeData}
            />
            <Button type="primary" style={{marginTop: '20px'}} onClick={onSave}>Save Workflow</Button>
        </div>
    );
};

const DraggableNode = ({ type, label }) => {
const WorkbenchPage = () => {
  const reactFlowWrapper = useRef(null);
  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    addNode,
  } = useWorkflowStore();
  const reactFlowInstance = useReactFlow();

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event) => {
      event.preventDefault();

      const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
      const type = event.dataTransfer.getData('application/reactflow-type');
      const label = event.dataTransfer.getData('application/reactflow-label');

      if (typeof type === 'undefined' || !type) {
        return;
      }

      const position = reactFlowInstance.project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });
      const newNode = {
        id: getId(),
        type,
        position,
        data: { label: label },
      };

      addNode(newNode);
    },
    [reactFlowInstance, addNode]
  );

  return (
    <Layout className="workbench-layout" style={{ height: 'calc(100vh - 112px)'}}>
      <Sider width={250} className="workbench-sider">
        <ComponentPalette />
        <Divider />
        <SceneManager />
      </Sider>
      <Content className="workbench-main">
        <div className="react-flow-wrapper" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onDrop={onDrop}
            onDragOver={onDragOver}
            fitView
          >
            <Controls />
            <Background />
          </ReactFlow>
        </div>
      </Content>
    </Layout>
  );
};

const WorkbenchPageWrapper = () => (
  <ReactFlowProvider>
    <WorkbenchPage />
  </ReactFlowProvider>
);

export default WorkbenchPageWrapper;
