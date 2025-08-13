from typing import List
from .node import Node
from .reach import Reach

class HydrodynamicNetwork:
    """
    Container for the entire hydrodynamic network topology.
    """
    def __init__(self):
        self.nodes: List[Node] = []
        self.reaches: List[Reach] = []

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

    def __repr__(self):
        return f"HydrodynamicNetwork(nodes={len(self.nodes)}, reaches={len(self.reaches)})"
