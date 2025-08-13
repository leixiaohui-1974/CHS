import create from 'zustand';
import { addEdge, applyNodeChanges, applyEdgeChanges } from 'reactflow';

const useWorkflowStore = create((set, get) => ({
  // State: The configuration object
  nodes: [], // These are the nodes for React Flow, derived from components
  edges: [], // These are the edges for React Flow, derived from connections
  components: [], // The ground truth for all components/nodes
  connections: [], // The ground truth for all connections/edges

  // Actions: Functions to manipulate the state
  onNodesChange: (changes) => {
    set({
      nodes: applyNodeChanges(changes, get().nodes),
    });
    // TODO: Sync changes back to the main `components` array if needed (e.g., position changes)
  },

  onEdgesChange: (changes) => {
    set({
      edges: applyEdgeChanges(changes, get().edges),
    });
  },

  addNode: (newNode) => {
    const newComponent = {
        id: newNode.id,
        type: newNode.data.label, // e.g., 'Reservoir'
        name: newNode.data.label,
        parameters: {}, // Default empty parameters
        dynamic_model: null,
        precision_model: null,
    };
    set((state) => ({
        nodes: [...state.nodes, newNode],
        components: [...state.components, newComponent],
    }));
  },

  removeNode: (nodeId) => {
    set((state) => ({
        nodes: state.nodes.filter(node => node.id !== nodeId),
        components: state.components.filter(comp => comp.id !== nodeId),
        // Also remove connected edges
        edges: state.edges.filter(edge => edge.source !== nodeId && edge.target !== nodeId),
        connections: state.connections.filter(conn => conn.source !== nodeId && conn.target !== nodeId),
    }));
  },

  onConnect: (connection) => {
    set((state) => ({
      edges: addEdge(connection, state.edges),
      connections: [...state.connections, connection],
    }));
  },

  // Example of how a component's parameters could be updated
  updateComponentParams: (nodeId, newParams) => {
    set((state) => ({
        components: state.components.map(comp =>
            comp.id === nodeId
            ? { ...comp, parameters: { ...comp.parameters, ...newParams } }
            : comp
        ),
    }));
  },

  // You can add more actions here, e.g., for loading a whole workflow
  loadWorkflow: (workflow) => {
    const { components, connections } = workflow;
    // Logic to convert components/connections to React Flow nodes/edges
    // This is a simplified example
    const nodes = components.map(comp => ({
        id: comp.id,
        type: 'default',
        data: { label: comp.name },
        position: comp.position || { x: Math.random() * 400, y: Math.random() * 400 },
    }));
    const edges = connections;

    set({ components, connections, nodes, edges });
  },

}));

export default useWorkflowStore;
