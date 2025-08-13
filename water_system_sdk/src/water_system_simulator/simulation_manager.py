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
    }

    @classmethod
    def get_class(cls, class_name: str):
        """Dynamically imports and returns a class from the registry."""
        if class_name not in cls._CLASS_MAP:
            raise ImportError(f"Component type '{class_name}' not found in registry.")

        module_path, class_name_only = cls._CLASS_MAP[class_name].rsplit('.', 1)

        try:
            # The root package is 'water_system_simulator'
            module = importlib.import_module(f".{module_path.split('.', 1)[1]}", package='water_system_simulator')
            return getattr(module, class_name_only)
        except (ImportError, AttributeError) as e:
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

        history = []

        for t in np.arange(0, total_time, dt):
            # 1. Process connections: transfer data between components
            for conn in connections:
                source_comp_name, source_attr_path = conn["source"].split('.', 1)
                target_comp_name, target_attr_path = conn["target"].split('.', 1)

                source_obj = self.components[source_comp_name]
                target_obj = self.components[target_comp_name]

                value = getattr_by_path(source_obj, source_attr_path)
                setattr_by_path(target_obj, target_attr_path, value)

            # 2. Execute components in the specified order
            for comp_name in execution_order:
                component = self.components[comp_name]
                component.step(dt=dt, t=t)

            # 3. Log data for this time step
            step_log = {"time": t}
            for log_path in logger_config:
                comp_name, attr_path = log_path.split('.', 1)
                value = getattr_by_path(self.components[comp_name], attr_path)
                step_log[log_path] = value
            history.append(step_log)

        return pd.DataFrame(history)
