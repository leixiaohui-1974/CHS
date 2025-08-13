from typing import List
from .node import Node
from .reach import Reach
from .structures import BaseStructure

class HydrodynamicNetwork:
    """
    Container for the entire hydrodynamic network topology, including nodes, reaches, and structures.
    """
    def __init__(self):
        self.nodes: List[Node] = []
        self.reaches: List[Reach] = []
        self.structures: List[BaseStructure] = []

    def add_node(self, node: Node):
        """Adds a node to the network."""
        if node not in self.nodes:
            self.nodes.append(node)

    def add_reach(self, reach: Reach):
        """Adds a reach to the network and ensures its nodes are also in the network."""
        if reach not in self.reaches:
            self.reaches.append(reach)
            self.add_node(reach.upstream_node)
            self.add_node(reach.downstream_node)

    def add_structure(self, structure: BaseStructure):
        """Adds a hydraulic structure to the network."""
        if structure not in self.structures:
            self.structures.append(structure)
            self.add_node(structure.upstream_node)
            self.add_node(structure.downstream_node)

    def __repr__(self):
        return (f"HydrodynamicNetwork(nodes={len(self.nodes)}, "
                f"reaches={len(self.reaches)}, structures={len(self.structures)})")
