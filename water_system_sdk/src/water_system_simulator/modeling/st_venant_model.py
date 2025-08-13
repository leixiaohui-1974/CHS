from .base_model import BaseModel
from ..hydrodynamics.network import HydrodynamicNetwork
from ..hydrodynamics.node import Node, JunctionNode, InflowBoundary, LevelBoundary
from ..hydrodynamics.reach import Reach
from ..hydrodynamics.structures import BaseStructure, WeirStructure
from ..hydrodynamics.solver import Solver
from typing import List, Dict, Any, Optional
from ..data_processing.processors import (
    BaseDataProcessor, DataCleaner, InverseDistanceWeightingInterpolator,
    ThiessenPolygonInterpolator, KrigingInterpolator, UnitConverter, TimeResampler
)

# A factory to map processor types from config to their classes
PROCESSOR_FACTORY: Dict[str, Any] = {
    "DataCleaner": DataCleaner,
    "InverseDistanceWeightingInterpolator": InverseDistanceWeightingInterpolator,
    "ThiessenPolygonInterpolator": ThiessenPolygonInterpolator,
    "KrigingInterpolator": KrigingInterpolator,
    "UnitConverter": UnitConverter,
    "TimeResampler": TimeResampler,
}


class StVenantModel(BaseModel):
    """
    A high-level wrapper for the 1D St. Venant equation solver.
    This model can be integrated into the CHS SDK SimulationManager and now
    supports internal data processing pipelines for its boundary conditions.
    """
    def __init__(self, nodes_data: List[Dict[str, Any]], reaches_data: List[Dict[str, Any]],
                 structures_data: List[Dict[str, Any]] = None, solver_params: Dict[str, Any] = None,
                 data_pipeline: Optional[List[Dict[str, Any]]] = None):
        """
        Initializes the St. Venant model from configuration dictionaries.

        Args:
            nodes_data (List[Dict]): A list of dictionaries, each describing a node.
            reaches_data (List[Dict]): A list of dictionaries, each describing a reach.
            structures_data (List[Dict]): A list of dictionaries, each describing a structure.
            solver_params (Dict): A dictionary of parameters for the solver.
            data_pipeline (Optional[List[Dict]]): Configuration for the data processing pipeline.
        """
        super().__init__()

        self.network = self._build_network(nodes_data, reaches_data, structures_data or [])
        self.nodes_map = {node.name: node for node in self.network.nodes}

        if solver_params is None:
            solver_params = {}
        self.solver = Solver(self.network, **solver_params)

        # Expose network entities for easy access and state reporting
        self.nodes = self.network.nodes
        self.reaches = self.network.reaches
        self.structures = self.network.structures

        # To hold raw data from external agents
        self.input: Dict[str, Any] = {}

        # Initialize the data processing pipeline
        self.data_pipeline: List[BaseDataProcessor] = []
        if data_pipeline:
            for step_config in data_pipeline:
                step_type = step_config.get("type")
                step_params = step_config.get("params", {})
                if step_type in PROCESSOR_FACTORY:
                    processor_class = PROCESSOR_FACTORY[step_type]
                    step_params['id'] = step_params.get('id', step_type)
                    self.data_pipeline.append(processor_class(**step_params))
                else:
                    raise ValueError(f"Unknown data processor type: {step_type}")

    def _build_network(self, nodes_data, reaches_data, structures_data) -> HydrodynamicNetwork:
        network = HydrodynamicNetwork()
        nodes_map = {}

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

        for r_data in reaches_data:
            r_data['upstream_node'] = nodes_map[r_data.pop('from_node')]
            r_data['downstream_node'] = nodes_map[r_data.pop('to_node')]
            reach = Reach(**r_data)
            network.add_reach(reach)

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

    def _execute_pipeline(self, raw_data: Any) -> Any:
        """Processes raw data through the configured pipeline."""
        processed_data = raw_data
        for processor in self.data_pipeline:
            processed_data = processor.process(processed_data)
        return processed_data

    def _update_boundaries(self):
        """
        Updates boundary conditions using data from the input attribute,
        processed through the pipeline.
        """
        # Example for a single inflow boundary. This can be made more generic.
        raw_inflow = self.input.get('raw_upstream_flow')
        if raw_inflow is not None:
            # The pipeline processes the value
            processed_inflow = self._execute_pipeline(raw_inflow)

            # The target node for this processed value needs to be identified.
            # Let's assume the config specifies the target node name.
            target_node_name = self.input.get('target_node')
            if target_node_name and target_node_name in self.nodes_map:
                node = self.nodes_map[target_node_name]
                if isinstance(node, InflowBoundary):
                    node.inflow = processed_inflow
                else:
                    print(f"Warning: Target node '{target_node_name}' is not an InflowBoundary.")
            else:
                # Fallback: Find the first inflow boundary and update it.
                for node in self.nodes:
                    if isinstance(node, InflowBoundary):
                        node.inflow = processed_inflow
                        break


    def step(self, dt: float, t: float = 0):
        """
        Advances the simulation by one time step.

        Args:
            dt (float): The time step duration in seconds.
            t (float): The current simulation time (optional).

        Returns:
            bool: True if the solver converged, False otherwise.
        """
        self._update_boundaries()
        success = self.solver.solve_step(dt)
        self.output = self.get_state() # Update output after step
        return success

    def get_state(self):
        """
        Returns a dictionary representing the current state of the network.
        """
        pipeline_state = {p.id: p.get_state() for p in self.data_pipeline}
        return {
            'nodes': {node.name: {'head': node.head, 'inflow': getattr(node, 'inflow', None)}
                      for node in self.nodes if isinstance(node, InflowBoundary)},
            'reaches': {reach.name: {'discharge': reach.discharge} for reach in self.reaches},
            'structures': {s.name: {'discharge': s.discharge} for s in self.structures},
            "data_pipeline_state": pipeline_state
        }
