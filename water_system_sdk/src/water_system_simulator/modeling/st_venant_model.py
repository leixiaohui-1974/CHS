from .base_model import BaseModel
from ..hydrodynamics.network import HydrodynamicNetwork
from ..hydrodynamics.node import Node, JunctionNode, InflowBoundary, LevelBoundary
from ..hydrodynamics.reach import Reach
from ..hydrodynamics.structures import BaseStructure, WeirStructure
from ..hydrodynamics.solver import Solver
from typing import List, Dict, Any

class StVenantModel(BaseModel):
    """
    A high-level wrapper for the 1D St. Venant equation solver.
    This model can be integrated into the CHS SDK SimulationManager.
    """
    def __init__(self, nodes_data: List[Dict[str, Any]], reaches_data: List[Dict[str, Any]],
                 structures_data: List[Dict[str, Any]] = None, solver_params: Dict[str, Any] = None):
        """
        Initializes the St. Venant model from configuration dictionaries.

        Args:
            nodes_data (List[Dict]): A list of dictionaries, each describing a node.
                                     e.g., {'name': 'n1', 'type': 'junction', 'bed_elevation': 5.0}
            reaches_data (List[Dict]): A list of dictionaries, each describing a reach.
                                       e.g., {'name': 'r1', 'from_node': 'n1', 'to_node': 'n2', ...}
            structures_data (List[Dict]): A list of dictionaries, each describing a structure.
            solver_params (Dict): A dictionary of parameters for the solver (e.g., tolerance).
        """
        super().__init__()

        self.network = self._build_network(nodes_data, reaches_data, structures_data or [])

        if solver_params is None:
            solver_params = {}
        self.solver = Solver(self.network, **solver_params)

        # Expose network entities for easy access and state reporting
        self.nodes = self.network.nodes
        self.reaches = self.network.reaches
        self.structures = self.network.structures

    def _build_network(self, nodes_data, reaches_data, structures_data) -> HydrodynamicNetwork:
        network = HydrodynamicNetwork()
        nodes_map = {}

        # Create node objects
        for n_data in nodes_data:
            node_type = n_data.pop('type', 'junction').lower()
            name = n_data['name']

            if node_type == 'junction':
                node = JunctionNode(**n_data)
            elif node_type == 'inflow':
                node = InflowBoundary(**n_data)
            elif node_type == 'level':
                node = LevelBoundary(**n_data)
            else:
                raise ValueError(f"Unknown node type: {node_type}")

            nodes_map[name] = node
            network.add_node(node)

        # Create reach objects
        for r_data in reaches_data:
            r_data['upstream_node'] = nodes_map[r_data.pop('from_node')]
            r_data['downstream_node'] = nodes_map[r_data.pop('to_node')]
            reach = Reach(**r_data)
            network.add_reach(reach)

        # Create structure objects
        for s_data in structures_data:
            s_data['upstream_node'] = nodes_map[s_data.pop('from_node')]
            s_data['downstream_node'] = nodes_map[s_data.pop('to_node')]
            struct_type = s_data.pop('type', 'weir').lower()

            if struct_type == 'weir':
                structure = WeirStructure(**s_data)
            else:
                raise ValueError(f"Unknown structure type: {struct_type}")

            network.add_structure(structure)

        return network

    def step(self, dt: float, t: float = 0):
        """
        Advances the simulation by one time step.

        Args:
            dt (float): The time step duration in seconds.
            t (float): The current simulation time (optional).

        Returns:
            bool: True if the solver converged, False otherwise.
        """
        success = self.solver.solve_step(dt)
        self.output = self.get_state() # Update output after step
        return success

    def get_state(self):
        """
        Returns a dictionary representing the current state of the network.
        """
        return {
            'nodes': {node.name: {'head': node.head} for node in self.nodes},
            'reaches': {reach.name: {'discharge': reach.discharge} for reach in self.reaches},
            'structures': {s.name: {'discharge': s.discharge} for s in self.structures}
        }
