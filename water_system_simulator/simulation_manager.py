import yaml
import csv
import importlib
import numpy as np
import os
import pandas as pd

from water_system_simulator.config_parser import parse_topology, parse_disturbances
from water_system_simulator.basic_tools.loggers import CSVLogger

def parse_control_params(file_path: str):
    """Parses the YAML control parameters file."""
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {}
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file: {e}")

class ComponentRegistry:
    """A registry for dynamically loading component classes."""
    _CLASS_MAP = {
        # Controllers
        "PIDController": "water_system_simulator.control.pid_controller.PIDController",
        "MPCController": "water_system_simulator.control.mpc_controller.MPCController",
        "KalmanFilter": "water_system_simulator.control.kalman_filter.KalmanFilter",
        # Models
        "ReservoirModel": "water_system_simulator.modeling.storage_models.ReservoirModel",
        "IntegralDelayModel": "water_system_simulator.modeling.storage_models.IntegralDelayModel",
        "FirstOrderInertiaModel": "water_system_simulator.modeling.storage_models.FirstOrderInertiaModel",
        "MuskingumChannelModel": "water_system_simulator.modeling.storage_models.MuskingumChannelModel",
        "ConstantHeadReservoir": "water_system_simulator.modeling.boundary_models.ConstantHeadReservoir",
        "GateStationModel": "water_system_simulator.modeling.control_structure_models.GateStationModel",
        "PumpStationModel": "water_system_simulator.modeling.control_structure_models.PumpStationModel",
        "HydropowerStationModel": "water_system_simulator.modeling.control_structure_models.HydropowerStationModel",
        "PipelineModel": "water_system_simulator.modeling.pipeline_model.PipelineModel",
        # Solvers
        "EulerIntegrator": "water_system_simulator.basic_tools.solvers.EulerIntegrator",
        "RK4Integrator": "water_system_simulator.basic_tools.rk4_solver.RK4Integrator"
    }

    @classmethod
    def get_class(cls, class_name: str):
        """Dynamically imports and returns a class from the registry."""
        if class_name not in cls._CLASS_MAP:
            raise ImportError(f"Component type '{class_name}' not found in registry.")

        module_path, class_name_only = cls._CLASS_MAP[class_name].rsplit('.', 1)

        try:
            module = importlib.import_module(module_path)
            return getattr(module, class_name_only)
        except (ImportError, AttributeError) as e:
            raise ImportError(f"Could not import class '{class_name}' from '{module_path}'. Error: {e}")

class SimulationManager:
    """
    Manages the setup and execution of a water system simulation.
    """
    def __init__(self, config: dict = None, case_path: str = None):
        """
        Initializes the simulation manager.

        Args:
            config (dict, optional): A dictionary containing the entire simulation configuration.
                                     If provided, `case_path` is ignored.
            case_path (str, optional): The path to a case directory containing configuration files.
                                       Used if `config` is not provided.
        """
        if config:
            print("Initializing simulation from configuration dictionary...")
            self._load_from_config_dict(config)
            self.case_path = "dict_config" # for logging prefix
        elif case_path:
            print(f"Initializing simulation for case: {case_path}...")
            self.case_path = case_path
            self._load_from_case_path()
        else:
            raise ValueError("Must provide either a 'config' dictionary or a 'case_path'.")

        self.components = {}
        self.component_order = []
        self.log_config = self.topology.get('logging', [])
        self.solver_class = None
        self.dt = self.topology.get('dt', 1.0)

        self._build_system()
        print("System built successfully.")

    def _load_from_config_dict(self, config: dict):
        """Loads configuration from a dictionary."""
        self.topology = config.get('topology', {})
        self.disturbances = config.get('disturbances', [])
        self.control_params = config.get('control_params', {})

    def _load_from_case_path(self):
        """Loads all necessary configuration files from a case path."""
        topology_path = os.path.join(self.case_path, 'topology.yml')
        disturbance_path = os.path.join(self.case_path, 'disturbances.csv')
        control_params_path = os.path.join(self.case_path, 'control_parameters.yaml')

        self.topology = parse_topology(topology_path)
        self.disturbances = parse_disturbances(disturbance_path)
        self.control_params = parse_control_params(control_params_path)

    def _build_system(self):
        """Constructs the system of components from the parsed topology."""
        solver_name = self.topology.get('solver', 'EulerIntegrator')
        self.solver_class = ComponentRegistry.get_class(solver_name)
        print(f"Using solver: {solver_name}")

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
            self._apply_control_params(name, comp_type, properties)

            component_class = ComponentRegistry.get_class(comp_type)

            # Inject solver and dt into properties for components that might need them.
            # The component's __init__ must accept **kwargs to ignore unused ones.
            properties['solver_class'] = self.solver_class
            properties['dt'] = self.dt

            self.components[name] = component_class(**properties)
            self.component_order.append(name)

    def _apply_control_params(self, name, comp_type, properties):
        """Applies control parameters to a component's properties."""
        if 'Controller' in comp_type:
            param_key_specific = f"{name}_params"
            if param_key_specific in self.control_params:
                properties.update(self.control_params[param_key_specific])
            else:
                param_key_generic = f"{comp_type.replace('Controller', '').lower()}_params"
                if param_key_generic in self.control_params:
                    properties.update(self.control_params[param_key_generic])

    def _get_connection_value(self, value_source: any, step_values: dict):
        """Gets a value for a connection from a component attribute or a constant."""
        if not isinstance(value_source, str):
            return value_source  # It's a constant

        if '.' not in value_source:
            raise ValueError(f"Invalid connection string: {value_source}.")

        if value_source in step_values:
            return step_values[value_source]

        comp_name, attr_name = value_source.split('.', 1)
        if comp_name not in self.components:
            raise ValueError(f"Component '{comp_name}' not found for connection '{value_source}'.")

        component = self.components[comp_name]
        return getattr(component, attr_name)

    def _initialize_run(self):
        """Initializes disturbance iterators for a simulation run."""
        disturbance_iterator = iter(self.disturbances)
        current_disturbance = next(disturbance_iterator, None)
        next_disturbance = next(disturbance_iterator, None)
        return disturbance_iterator, current_disturbance, next_disturbance

    def _process_step(self, t, step_values, current_disturbance):
        """Processes a single time step for all components."""
        if current_disturbance:
            for key, value in current_disturbance.items():
                if key != 'time':
                    step_values[f"{key}.output"] = value

        for comp_name in self.component_order:
            # Find the component's configuration dictionary
            config = next((c for c in self.topology['components'] if c['name'] == comp_name), None)
            if not config:
                raise ValueError(f"Configuration for component '{comp_name}' not found.")

            comp_type = config['type']

            if comp_type == 'SummingPoint':
                self._process_summing_point(config, step_values)
            elif comp_type != 'Disturbance':
                self._process_component(config, comp_name, t, step_values)

    def _process_summing_point(self, config, step_values):
        """Calculates the output of a SummingPoint."""
        connections = config.get('connections', [])
        gains = config.get('gains', [1.0] * len(connections))
        sum_val = sum(self._get_connection_value(conn, step_values) * gain for conn, gain in zip(connections, gains))
        step_values[f"{config['name']}.output"] = sum_val

    def _process_component(self, config, comp_name, t, step_values):
        """Calculates the output of a regular component."""
        component = self.components[comp_name]
        if not hasattr(component, 'step'):
            return

        method = getattr(component, 'step')
        kwargs = {}
        connections = config.get('connections', {})
        for param_name, value_source in connections.items():
            if isinstance(value_source, list):
                kwargs[param_name] = np.array([self._get_connection_value(v, step_values) for v in value_source])
            else:
                kwargs[param_name] = self._get_connection_value(value_source, step_values)

        kwargs['t'] = t
        kwargs['dt'] = self.dt
        method(**kwargs)
        step_values[f"{comp_name}.output"] = component.output

    def _log_step_data(self, t: float, step_values: dict) -> dict:
        """Constructs a dictionary of the data to be logged for the current step."""
        log_data = {}
        for log_key in self.log_config:
            if log_key == 'time':
                log_data['time'] = t
            else:
                log_data[log_key] = self._get_connection_value(log_key, step_values)
        return log_data

    def run(self, duration: int, log_to_file: bool = False, log_file_prefix: str = None) -> pd.DataFrame:
        """
        Runs the simulation for a given duration.

        Args:
            duration (int): The total duration of the simulation in seconds.
            log_to_file (bool, optional): If True, saves the results to a CSV file. Defaults to False.
            log_file_prefix (str, optional): The prefix for the log file name.
                                             If not provided, defaults to the case name.

        Returns:
            pd.DataFrame: A DataFrame containing the simulation results.
        """
        if not log_file_prefix:
            log_file_prefix = os.path.basename(os.path.normpath(self.case_path))

        print(f"Starting simulation for '{log_file_prefix}', duration={duration}s, dt={self.dt}s...")
        n_steps = int(duration / self.dt)

        dist_iter, curr_dist, next_dist = self._initialize_run()

        results_history = []

        for i in range(n_steps):
            t = i * self.dt
            step_values = {'time': t}

            if next_dist and t >= next_dist['time']:
                curr_dist = next_dist
                next_dist = next(dist_iter, None)

            self._process_step(t, step_values, curr_dist)

            # Log data for this step
            if self.log_config:
                step_log_data = self._log_step_data(t, step_values)
                results_history.append(step_log_data)

        # Convert results to DataFrame
        results_df = pd.DataFrame(results_history)

        if log_to_file:
            if not os.path.exists('results'):
                os.makedirs('results')
            log_file = os.path.join('results', f"{log_file_prefix}_log.csv")
            results_df.to_csv(log_file, index=False)
            print(f"Simulation complete. Log saved to {log_file}")
        else:
            print("Simulation complete.")

        return results_df
