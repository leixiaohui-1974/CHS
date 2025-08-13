import { create } from 'zustand';

const useKnowledgeGraphStore = create((set) => ({
  highlightedNodeId: null,
  setHighlightedNodeId: (nodeId) => set({ highlightedNodeId: nodeId }),
  clearHighlight: () => set({ highlightedNodeId: null }),
}));

export default useKnowledgeGraphStore;
