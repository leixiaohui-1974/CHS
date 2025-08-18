import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, {
  Controls,
  Background,
  applyNodeChanges,
  applyEdgeChanges,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { getSystemTopology } from '../services/apiService'; // Assuming this service exists

// Mock data for initial layout, in case the API doesn't provide positions
const initialNodes = [
  { id: '1', position: { x: 100, y: 100 }, data: { label: 'Loading...' } },
];
const initialEdges = [];

const ReactFlowTopology = () => {
  const [nodes, setNodes] = useState(initialNodes);
  const [edges, setEdges] = useState(initialEdges);
  const [error, setError] = useState(null);

  const onNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    [setNodes]
  );
  const onEdgesChange = useCallback(
    (changes) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    [setEdges]
  );

  useEffect(() => {
    const fetchTopology = async () => {
      try {
        // TODO: The backend API needs to provide positional data.
        // For now, we assume the API response has a structure like:
        // {
        //   nodes: [{ id, label, type, position: {x, y} }],
        //   edges: [{ id, source, target }]
        // }
        const data = await getSystemTopology();

        const flowNodes = data.nodes.map((node, index) => ({
          id: node.id,
          position: node.position || { x: (index % 5) * 200, y: Math.floor(index / 5) * 150 },
          data: { label: `${node.label} (${node.type})` },
        }));

        const flowEdges = data.edges.map(edge => ({
          id: `e-${edge.from}-${edge.to}`,
          source: edge.from,
          target: edge.to,
          animated: true,
        }));

        setNodes(flowNodes);
        setEdges(flowEdges);
      } catch (err) {
        setError('Failed to load system topology. Please ensure the backend is running and the project is selected.');
        console.error(err);
      }
    };
    fetchTopology();
  }, []);

  if (error) {
    return <p style={{ color: 'red', textAlign: 'center', padding: '20px' }}>{error}</p>;
  }

  return (
    <div style={{ height: '100%', width: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        proOptions={{ hideAttribution: true }} // Hides the "React Flow" attribution
      >
        <Controls />
        <Background />
      </ReactFlow>
    </div>
  );
};

export default ReactFlowTopology;
