import pandas as pd
import numpy as np
import importlib
import functools
from typing import Dict, Any, List

# --- Helper functions for attribute access ---

def getattr_by_path(obj: Any, path: str) -> Any:
    """Access a nested attribute using a dot-separated path."""
    try:
        return functools.reduce(getattr, path.split('.'), obj)
    except AttributeError:
        raise AttributeError(f"Could not find attribute '{path}' in object {obj}.")

def setattr_by_path(obj: Any, path: str, value: Any):
    """Set a nested attribute using a dot-separated path."""
    parts = path.split('.')
    try:
        parent = functools.reduce(getattr, parts[:-1], obj)
        setattr(parent, parts[-1], value)
    except AttributeError:
        raise AttributeError(f"Could not find parent object for attribute '{path}'.")

# --- Component Registry ---

class ComponentRegistry:
    """A registry for dynamically loading component classes."""
    _CLASS_MAP = {
        # Controllers
        "PIDController": "water_system_simulator.control.pid_controller.PIDController",
        # Disturbances
        "Disturbance": "water_system_simulator.disturbances.predefined.Disturbance",
        "RainfallAgent": "water_system_simulator.disturbances.agents.RainfallAgent",
        "DemandAgent": "water_system_simulator.disturbances.agents.DemandAgent",
        "PriceAgent": "water_system_simulator.disturbances.agents.PriceAgent",
        "FaultAgent": "water_system_simulator.disturbances.agents.FaultAgent",
        # Models
        "ReservoirModel": "water_system_simulator.modeling.storage_models.ReservoirModel",
        "MuskingumChannelModel": "water_system_simulator.modeling.storage_models.MuskingumChannelModel",
        "FirstOrderInertiaModel": "water_system_simulator.modeling.storage_models.FirstOrderInertiaModel",
        "IntegralDelayModel": "water_system_simulator.modeling.delay_models.IntegralDelayModel",
        "GateStationModel": "water_system_simulator.modeling.control_structure_models.GateStationModel",
        # Instruments
        "LevelSensor": "water_system_simulator.modeling.instrument_models.LevelSensor",
        "GateActuator": "water_system_simulator.modeling.instrument_models.GateActuator",
    }

    @classmethod
    def get_class(cls, class_name: str):
        """Dynamically imports and returns a class from the registry."""
        if class_name not in cls._CLASS_MAP:
            raise ImportError(f"Component type '{class_name}' not found in registry.")

        module_path, class_name_only = cls._CLASS_MAP[class_name].rsplit('.', 1)

        try:
            # First, try to import it as if it's part of the SDK package
            if 'water_system_simulator' in module_path:
                relative_module_path = module_path.split('.', 1)[1]
                module = importlib.import_module(f".{relative_module_path}", package='water_system_simulator')
                return getattr(module, class_name_only)
            else:
                # If not, try a direct, absolute import (for extensions/tests)
                module = importlib.import_module(module_path)
                return getattr(module, class_name_only)
        except (ImportError, AttributeError, IndexError) as e:
            raise ImportError(f"Could not import class '{class_name_only}' from '{module_path}'. Error: {e}")

# --- Simulation Manager ---

class SimulationManager:
    """
    Manages the setup and execution of a water system simulation based on a
    configuration dictionary. This manager is stateless and can be reused to
    run multiple simulations.
    """
    def __init__(self):
        """Initializes the simulation manager."""
        self.components: Dict[str, Any] = {}
        self.config: Dict[str, Any] = {}

    def _build_system(self):
        """Constructs the system of components from the configuration."""
        if "components" not in self.config:
            raise ValueError("Configuration must contain a 'components' dictionary.")

        component_configs = self.config["components"]
        for name, comp_info in component_configs.items():
            comp_type = comp_info["type"]
            params = comp_info.get("params", {})

            component_class = ComponentRegistry.get_class(comp_type)
            self.components[name] = component_class(**params)

    def _execute_step(self, instruction: Any, t: float, dt: float):
        """Executes a single instruction from the execution_order."""
        if isinstance(instruction, str):
            # It's a simple component name, call the standard step method
            self.components[instruction].step(dt=dt, t=t)
        elif isinstance(instruction, dict):
            # It's a detailed instruction for a method call
            comp_name = instruction["component"]
            method_name = instruction["method"]

            # Prepare arguments for the method call
            args = {}
            for arg_name, source_path in instruction.get("args", {}).items():
                if source_path == "simulation.dt":
                    args[arg_name] = dt
                elif source_path == "simulation.t":
                    args[arg_name] = t
                else:
                    source_comp, source_attr = source_path.split('.', 1)
                    args[arg_name] = getattr_by_path(self.components[source_comp], source_attr)

            # Get the component and its method
            component = self.components[comp_name]
            method = getattr(component, method_name)

            # Call the method
            result = method(**args)

            # Store the result if a destination is specified
            if "result_to" in instruction and result is not None:
                target_comp, target_attr = instruction["result_to"].split('.', 1)
                setattr_by_path(self.components[target_comp], target_attr, result)
        else:
            raise TypeError(f"Unsupported instruction type in execution_order: {type(instruction)}")

    def run(self, config: Dict[str, Any]) -> pd.DataFrame:
        """
        Runs the simulation according to the provided configuration.

        Args:
            config: A dictionary defining the components, connections, and
                    simulation parameters.

        Returns:
            A pandas DataFrame containing the simulation log.
        """
        # Reset state for the new run
        self.config = config
        self.components = {}
        self._build_system()

        sim_params = self.config.get("simulation_params", {})
        total_time = sim_params.get("total_time", 100)
        dt = sim_params.get("dt", 1.0)

        connections = self.config.get("connections", [])
        execution_order = self.config.get("execution_order", [])
        logger_config = self.config.get("logger_config", [])

        if not execution_order:
            raise ValueError("'execution_order' cannot be empty.")

        history = []

        for t in np.arange(0, total_time, dt):
            # 1. Process connections (for simple, state-copying links)
            for conn in connections:
                source_comp_name, source_attr_path = conn["source"].split('.', 1)
                target_comp_name, target_attr_path = conn["target"].split('.', 1)
                value = getattr_by_path(self.components[source_comp_name], source_attr_path)
                setattr_by_path(self.components[target_comp_name], target_attr_path, value)

            # 2. Execute components based on the new expressive execution order
            for instruction in execution_order:
                self._execute_step(instruction, t=t, dt=dt)

            # 3. Log data for this time step
            step_log = {"time": t}
            for log_path in logger_config:
                comp_name, attr_path = log_path.split('.', 1)
                value = getattr_by_path(self.components[comp_name], attr_path)
                step_log[log_path] = value
            history.append(step_log)

        return pd.DataFrame(history)
