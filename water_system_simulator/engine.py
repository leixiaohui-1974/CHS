import yaml
import csv
import importlib
import numpy as np
import inspect

from water_system_simulator.config_parser import parse_topology, parse_disturbances
from water_system_simulator.basic_tools.loggers import CSVLogger

class Simulator:
    """
    Generic Water System Simulator Engine.
    """
    def __init__(self, topology_path: str, disturbance_path: str = None):
        """
        Initializes the simulator.
        """
        print("Initializing simulator...")
        self.topology = parse_topology(topology_path)
        self.disturbances = parse_disturbances(disturbance_path) if disturbance_path else []

        self.components = {}
        self.component_order = []
        self.log_config = self.topology.get('logging', [])

        self._build_system()
        print("System built successfully.")

    def _get_class_from_string(self, class_name: str):
        """Dynamically imports a class from a string name."""
        # A mapping from class names to their modules
        module_map = {
            'IntegralDelayModel': 'water_system_simulator.modeling.storage_models',
            'FirstOrderInertiaModel': 'water_system_simulator.modeling.storage_models',
            'GateModel': 'water_system_simulator.modeling.control_structure_models',
            'PumpModel': 'water_system_simulator.modeling.control_structure_models',
            'PIDController': 'water_system_simulator.control.pid_controller',
            'MPCController': 'water_system_simulator.control.mpc_controller',
            'KalmanFilter': 'water_system_simulator.control.kalman_filter',
        }
        try:
            module_path = module_map[class_name]
            module = importlib.import_module(module_path)
            return getattr(module, class_name)
        except (KeyError, ImportError, AttributeError) as e:
            raise ImportError(f"Could not import class '{class_name}'. Ensure it is in the module_map. Error: {e}")

    def _build_system(self):
        """
        Constructs the system of components from the parsed topology.
        The order of components in the YAML file determines the execution order.
        """
        component_configs = self.topology.get('components', [])
        if not component_configs:
            raise ValueError("No components defined in topology file.")

        for config in component_configs:
            name = config['name']
            comp_type = config['type']

            # Skip placeholder disturbance or internal components
            if comp_type in ['Disturbance', 'SummingPoint']:
                self.component_order.append(name)
                continue

            properties = config.get('properties', {})
            component_class = self._get_class_from_string(comp_type)
            self.components[name] = component_class(**properties)
            self.component_order.append(name)

    def _get_connection_value(self, value_source: any, step_values: dict):
        """
        Gets a value for a connection.
        If the source is not a string, it's treated as a constant.
        If it is a string, it's treated as a link to another component's attribute
        or a value calculated in the current step.
        e.g., 'tank1.storage' or 5.0
        """
        if not isinstance(value_source, str):
            # It's a constant value
            return value_source

        value_str = value_source
        if '.' not in value_str:
             raise ValueError(f"Invalid connection string: {value_str}. Must be 'component_name.attribute_name'.")

        # Prioritize values calculated in the current time step (like disturbances or component outputs)
        if value_str in step_values:
            return step_values[value_str]

        # Otherwise, get the attribute directly from a component object (state from previous step)
        comp_name, attr_name = value_str.split('.', 1)
        if comp_name not in self.components:
            raise ValueError(f"Component '{comp_name}' not found in the system.")

        component = self.components[comp_name]
        if not hasattr(component, attr_name):
             raise AttributeError(f"Component '{comp_name}' does not have an attribute '{attr_name}'.")
        return getattr(component, attr_name)

    def run(self, duration: int, dt: float, log_file: str):
        """
        Runs the simulation.
        """
        print(f"Starting simulation for {duration}s with dt={dt}s...")
        n_steps = int(duration / dt)

        # Setup Logger
        logger = CSVLogger(f"results/{log_file}", self.log_config)

        # Prepare disturbance data iterator
        disturbance_iterator = iter(self.disturbances)
        current_disturbance = next(disturbance_iterator, None)
        next_disturbance = next(disturbance_iterator, None)

        # Main simulation loop
        for i in range(n_steps):
            t = i * dt
            step_values = {'time': t} # Holds outputs from the current step

            # --- Update disturbances for the current time step ---
            # Forward-fill interpolation for disturbances
            if next_disturbance and t >= next_disturbance['time']:
                current_disturbance = next_disturbance
                next_disturbance = next(disturbance_iterator, None)

            # Populate step_values with disturbance outputs
            if current_disturbance:
                for key, value in current_disturbance.items():
                    if key != 'time':
                        # This assumes the disturbance component name in the YAML
                        # matches the column header in the CSV.
                        # e.g., component 'upstream_inflow' matches 'upstream_inflow' column
                        # The output is stored as 'upstream_inflow.output'
                        step_values[f"{key}.output"] = value


            # Execute components in the specified order
            for comp_name in self.component_order:
                config = self.topology['components'][self.component_order.index(comp_name)]
                comp_type = config['type']

                # Handle internal component types
                if comp_type == 'SummingPoint':
                    connections = config.get('connections', [])
                    gains = config.get('gains', [1.0] * len(connections))
                    sum_val = 0
                    for i, conn_str in enumerate(connections):
                        val = self._get_connection_value(conn_str, step_values)
                        sum_val += val * gains[i]
                    step_values[f"{comp_name}.output"] = sum_val
                    continue

                # Skip placeholder disturbance components
                if comp_type == 'Disturbance':
                    continue

                component = self.components[comp_name]

                # Find the primary method (step or calculate)
                method_name = None
                if hasattr(component, 'step'):
                    method_name = 'step'
                elif hasattr(component, 'calculate'):
                    method_name = 'calculate'

                if not method_name:
                    continue # This component doesn't have a step/calculate method

                method = getattr(component, method_name)
                method_params = inspect.signature(method).parameters

                # Prepare kwargs for the method call from connections
                kwargs = {}
                connections = self.topology['components'][self.component_order.index(comp_name)].get('connections', {})
                for param_name, value_source in connections.items():
                    if param_name in method_params:
                        if isinstance(value_source, list):
                            # Handle vector inputs by resolving each item in the list
                            kwargs[param_name] = np.array([self._get_connection_value(v_src, step_values) for v_src in value_source])
                        else:
                            # Handle scalar inputs
                            kwargs[param_name] = self._get_connection_value(value_source, step_values)

                # Add dt if the method requires it
                if 'dt' in method_params:
                    kwargs['dt'] = dt

                # Execute the method
                output = method(**kwargs)

                # Store the output value for use by subsequent components in this step
                # We store it under a generic 'output' key for simplicity
                # The connection string will be e.g., 'pid_controller.output'
                step_values[f"{comp_name}.output"] = output

                # Also update the component's own 'output' attribute if it exists
                if hasattr(component, 'output'):
                    component.output = output


            # Log data for this time step
            log_row = []
            for log_key in self.log_config:
                if log_key == 'time':
                    log_row.append(t)
                else:
                    log_row.append(self._get_connection_value(log_key, step_values))
            logger.log(log_row)

        print(f"Simulation complete. Log saved to results/{log_file}")
