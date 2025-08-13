import React, { useRef, useCallback } from 'react';
import { Layout, Tree, Divider, Typography, Button } from 'antd';
import { MapContainer, TileLayer } from 'react-leaflet';
import ReactFlow, {
  ReactFlowProvider,
  Controls,
  useReactFlow,
} from 'reactflow';
import useWorkflowStore from '../store/useWorkflowStore';
import PropertiesPanel from '../components/PropertiesPanel';
import 'reactflow/dist/style.css';
import 'leaflet/dist/leaflet.css';
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
    const { nodes, components, connections, setSelectedNodeId } = useWorkflowStore();
    const reactFlowInstance = useReactFlow();

    const treeData = [
        {
          title: 'Scene Root',
          key: '0-0',
          children: nodes.map(node => ({ title: node.data.label, key: node.id })),
        },
    ];

    const onSave = () => {
        const topology = {
            components: components.map(comp => {
                // Find connections for the current component
                const compConnections = connections
                    .filter(conn => conn.source === comp.id || conn.target === comp.id)
                    .map(conn => ({
                        source: components.find(c => c.id === conn.source)?.name,
                        target: components.find(c => c.id === conn.target)?.name,
                    }));

                return {
                    name: comp.name,
                    type: comp.type,
                    properties: comp.parameters,
                    // A more sophisticated mapping would be needed for real scenarios
                    connections: compConnections,
                };
            })
        };

        console.log('Generated Topology Object:', JSON.stringify(topology, null, 2));
        alert('Generated topology object has been logged to the console.');
        // Here you would typically send this JSON to a backend API
    };

    const onSelect = (selectedKeys) => {
        if (selectedKeys.length > 0) {
            const nodeId = selectedKeys[0];
            setSelectedNodeId(nodeId);
            reactFlowInstance.fitView({ nodes: [{ id: nodeId }], duration: 300 });
        }
    };

    return (
        <div>
            <Title level={4}>Scene Manager</Title>
            <Tree
              showLine
              defaultExpandedKeys={['0-0']}
              treeData={treeData}
              onSelect={onSelect}
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
    setSelectedNodeId,
  } = useWorkflowStore();
  const reactFlowInstance = useReactFlow();

  const handleNodeClick = (event, node) => {
    setSelectedNodeId(node.id);
  };

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
      <Sider width={250} className="workbench-sider" theme="light">
        <ComponentPalette />
        <Divider />
        <SceneManager />
      </Sider>
      <Content className="workbench-main">
        <div className="react-flow-wrapper" ref={reactFlowWrapper}>
          <MapContainer center={[30.5, 114.3]} zoom={10} style={{ height: '100%', width: '100%' }}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onDrop={onDrop}
              onDragOver={onDragOver}
              onNodeClick={handleNodeClick}
              fitView
              style={{ background: 'transparent' }}
            >
              <Controls />
            </ReactFlow>
          </MapContainer>
        </div>
      </Content>
      <Sider width={300} className="workbench-sider" theme="light">
        <PropertiesPanel />
      </Sider>
    </Layout>
  );
};

const WorkbenchPageWrapper = () => (
  <ReactFlowProvider>
    <WorkbenchPage />
  </ReactFlowProvider>
);

export default WorkbenchPageWrapper;
