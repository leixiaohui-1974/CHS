import yaml
import csv
import importlib
import numpy as np
import inspect
import os

from water_system_simulator.config_parser import parse_topology, parse_disturbances
from water_system_simulator.basic_tools.loggers import CSVLogger

def parse_control_params(file_path: str):
    """Parses the YAML control parameters file."""
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {} # It's okay if this file doesn't exist
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file: {e}")


class Simulator:
    """
    Generic Water System Simulator Engine.
    """
    def __init__(self, case_path: str):
        """
        Initializes the simulator from a case directory.
        """
        print(f"Initializing simulator for case: {case_path}...")
        self.case_path = case_path

        # Construct file paths
        topology_path = os.path.join(case_path, 'topology.yml')
        disturbance_path = os.path.join(case_path, 'disturbances.csv')
        control_params_path = os.path.join(case_path, 'control_parameters.yaml')

        self.topology = parse_topology(topology_path)
        self.disturbances = parse_disturbances(disturbance_path)
        self.control_params = parse_control_params(control_params_path)

        self.components = {}
        self.component_order = []
        self.log_config = self.topology.get('logging', [])

        self._build_system()
        print("System built successfully.")

    def _get_class_from_string(self, class_name: str):
        """Dynamically imports a class from a string name."""
        # This logic can be expanded for more modules
        if 'Controller' in class_name:
            module_path = f"water_system_simulator.control.{class_name.replace('Controller', '_controller').lower()}"
        elif 'Model' in class_name:
            if 'Pipeline' in class_name:
                module_path = 'water_system_simulator.modeling.pipeline_model'
            elif any(k in class_name for k in ['Gate', 'Pump', 'Hydropower']):
                 module_path = 'water_system_simulator.modeling.control_structure_models'
            else:
                 module_path = 'water_system_simulator.modeling.storage_models'
        elif 'Filter' in class_name:
            module_path = 'water_system_simulator.control.kalman_filter'
        else:
            raise ImportError(f"Unknown component type for class name: {class_name}")

        try:
            module = importlib.import_module(module_path)
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            raise ImportError(f"Could not import class '{class_name}' from '{module_path}'. Error: {e}")

    def _build_system(self):
        """
        Constructs the system of components from the parsed topology and applies control parameters.
        """
        component_configs = self.topology.get('components', [])
        if not component_configs:
            raise ValueError("No components defined in topology file.")

        for config in component_configs:
            name = config['name']
            comp_type = config['type']

            if comp_type in ['Disturbance', 'SummingPoint']:
                self.component_order.append(name)
                continue

            properties = config.get('properties', {})

            # If it's a controller, inject parameters from control_parameters.yaml
            if 'Controller' in comp_type:
                # First, try to find parameters matching the component's specific name
                param_key_specific = f"{name}_params"
                if param_key_specific in self.control_params:
                    properties.update(self.control_params[param_key_specific])
                else:
                    # If not found, fall back to a generic key based on the class type
                    param_key_generic = f"{comp_type.replace('Controller', '').lower()}_params"
                    if param_key_generic in self.control_params:
                        properties.update(self.control_params[param_key_generic])

            component_class = self._get_class_from_string(comp_type)
            self.components[name] = component_class(**properties)
            self.component_order.append(name)

    def _get_connection_value(self, value_source: any, step_values: dict):
        """
        Gets a value for a connection from a component attribute or a constant.
        """
        if not isinstance(value_source, str):
            return value_source # It's a constant

        value_str = value_source
        if '.' not in value_str:
             raise ValueError(f"Invalid connection string: {value_str}.")

        if value_str in step_values:
            return step_values[value_str]

        comp_name, attr_name = value_str.split('.', 1)
        if comp_name not in self.components:
            raise ValueError(f"Component '{comp_name}' not found.")

        component = self.components[comp_name]
        if not hasattr(component, attr_name):
             raise AttributeError(f"Component '{comp_name}' has no attribute '{attr_name}'.")
        return getattr(component, attr_name)

    def run(self, duration: int, dt: float, log_file_prefix: str):
        """
        Runs the simulation.
        """
        log_file = f"{log_file_prefix}_log.csv"
        print(f"Starting simulation for {self.case_path}, duration={duration}s, dt={dt}s...")
        n_steps = int(duration / dt)

        logger = CSVLogger(os.path.join('results', log_file), self.log_config)

        disturbance_iterator = iter(self.disturbances)
        current_disturbance = next(disturbance_iterator, None)
        next_disturbance = next(disturbance_iterator, None)

        for i in range(n_steps):
            t = i * dt
            step_values = {'time': t}

            if next_disturbance and t >= next_disturbance['time']:
                current_disturbance = next_disturbance
                next_disturbance = next(disturbance_iterator, None)

            if current_disturbance:
                for key, value in current_disturbance.items():
                    if key != 'time':
                        step_values[f"{key}.output"] = value

            for comp_name in self.component_order:
                config = self.topology['components'][self.component_order.index(comp_name)]
                comp_type = config['type']

                if comp_type == 'SummingPoint':
                    connections = config.get('connections', [])
                    gains = config.get('gains', [1.0] * len(connections))
                    sum_val = 0
                    for j, conn_str in enumerate(connections):
                        val = self._get_connection_value(conn_str, step_values)
                        sum_val += val * gains[j]
                    step_values[f"{comp_name}.output"] = sum_val
                    continue

                if comp_type == 'Disturbance':
                    continue

                component = self.components[comp_name]

                method_name = 'step' if hasattr(component, 'step') else 'calculate'
                if not hasattr(component, method_name):
                    continue

                method = getattr(component, method_name)
                method_params = inspect.signature(method).parameters

                kwargs = {}
                connections = config.get('connections', {})
                for param_name, value_source in connections.items():
                    if param_name in method_params:
                        if isinstance(value_source, list):
                            kwargs[param_name] = np.array([self._get_connection_value(v_src, step_values) for v_src in value_source])
                        else:
                            kwargs[param_name] = self._get_connection_value(value_source, step_values)

                if 'dt' in method_params:
                    kwargs['dt'] = dt

                output = method(**kwargs)
                step_values[f"{comp_name}.output"] = output

            log_row = []
            for log_key in self.log_config:
                if log_key == 'time':
                    log_row.append(t)
                else:
                    log_row.append(self._get_connection_value(log_key, step_values))
            logger.log(log_row)

        print(f"Simulation complete. Log saved to results/{log_file}")
