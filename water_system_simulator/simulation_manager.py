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
    Manages the setup and execution of a water system simulation based on configuration files.
    """
    def __init__(self, case_path: str):
        """
        Initializes the simulation manager from a case directory.
        """
        print(f"Initializing simulation for case: {case_path}...")
        self.case_path = case_path
        self._load_configs()

        self.components = {}
        self.component_order = []
        self.log_config = self.topology.get('logging', [])
        self.solver_class = None
        self.dt = self.topology.get('dt', 1.0)

        self._build_system()
        print("System built successfully.")

    def _load_configs(self):
        """Loads all necessary configuration files."""
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

            if 'solver_class' in inspect.signature(component_class.__init__).parameters:
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

    def _initialize_run(self, log_file_prefix: str):
        """Initializes logging and disturbance iterators for a simulation run."""
        log_file = f"{log_file_prefix}_log.csv"
        logger = CSVLogger(os.path.join('results', log_file), self.log_config)

        disturbance_iterator = iter(self.disturbances)
        current_disturbance = next(disturbance_iterator, None)
        next_disturbance = next(disturbance_iterator, None)

        return logger, disturbance_iterator, current_disturbance, next_disturbance

    def _process_step(self, t, step_values, current_disturbance):
        """Processes a single time step for all components."""
        if current_disturbance:
            for key, value in current_disturbance.items():
                if key != 'time':
                    step_values[f"{key}.output"] = value

        for comp_name in self.component_order:
            config = self.topology['components'][self.component_order.index(comp_name)]
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
        method_name = 'step' if hasattr(component, 'step') else 'calculate'
        if not hasattr(component, method_name):
            return

        method = getattr(component, method_name)
        method_params = inspect.signature(method).parameters

        kwargs = {}
        connections = config.get('connections', {})
        for param_name, value_source in connections.items():
            if param_name in method_params:
                if isinstance(value_source, list):
                    kwargs[param_name] = np.array([self._get_connection_value(v, step_values) for v in value_source])
                else:
                    kwargs[param_name] = self._get_connection_value(value_source, step_values)

        if 'dt' in method_params: kwargs['dt'] = self.dt
        if 't' in method_params: kwargs['t'] = t

        method(**kwargs)
        step_values[f"{comp_name}.output"] = component.output

    def _log_step(self, logger, t, step_values):
        """Logs the required values for the current time step."""
        log_row = []
        for log_key in self.log_config:
            if log_key == 'time':
                log_row.append(t)
            else:
                log_row.append(self._get_connection_value(log_key, step_values))
        logger.log(log_row)

    def run(self, duration: int, log_file_prefix: str):
        """Runs the simulation for a given duration."""
        print(f"Starting simulation for {self.case_path}, duration={duration}s, dt={self.dt}s...")
        n_steps = int(duration / self.dt)

        logger, dist_iter, curr_dist, next_dist = self._initialize_run(log_file_prefix)

        for i in range(n_steps):
            t = i * self.dt
            step_values = {'time': t}

            if next_dist and t >= next_dist['time']:
                curr_dist = next_dist
                next_dist = next(dist_iter, None)

            self._process_step(t, step_values, curr_dist)
            self._log_step(logger, t, step_values)

        print(f"Simulation complete. Log saved to results/{log_file_prefix}_log.csv")
