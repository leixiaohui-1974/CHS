import pandas as pd
import numpy as np
import importlib
import functools
from typing import Dict, Any, List

# --- Helper functions for attribute access ---

def getattr_by_path(obj: Any, path: str) -> Any:
    """Access a nested attribute or dictionary key using a dot-separated path."""
    def _get_attr_or_key(current_obj, key):
        if isinstance(current_obj, dict):
            try:
                return current_obj[key]
            except KeyError:
                raise AttributeError(f"Dictionary does not have key '{key}'")
        else:
            return getattr(current_obj, key)
    try:
        return functools.reduce(_get_attr_or_key, path.split('.'), obj)
    except (AttributeError, KeyError):
        raise AttributeError(f"Could not find attribute or key '{path}' in object {obj}.")


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
        # Preprocessing
        "RainfallProcessor": "water_system_simulator.preprocessing.rainfall_processor.RainfallProcessor",
        "InverseDistanceWeightingInterpolator": "water_system_simulator.preprocessing.interpolators.InverseDistanceWeightingInterpolator",
        "ThiessenPolygonInterpolator": "water_system_simulator.preprocessing.interpolators.ThiessenPolygonInterpolator",
        "KrigingInterpolator": "water_system_simulator.preprocessing.interpolators.KrigingInterpolator",
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
        "SemiDistributedHydrologyModel": "water_system_simulator.modeling.hydrology.semi_distributed.SemiDistributedHydrologyModel",
        # Runoff Models
        "RunoffCoefficientModel": "water_system_simulator.modeling.hydrology.runoff_models.RunoffCoefficientModel",
        "XinanjiangModel": "water_system_simulator.modeling.hydrology.runoff_models.XinanjiangModel",
        "SCSRunoffModel": "water_system_simulator.modeling.hydrology.runoff_models.SCSRunoffModel",
        "TankModel": "water_system_simulator.modeling.hydrology.runoff_models.TankModel",
        "HYMODModel": "water_system_simulator.modeling.hydrology.runoff_models.HYMODModel",
        "GreenAmptRunoffModel": "water_system_simulator.modeling.hydrology.runoff_models.GreenAmptRunoffModel",
        "TOPMODEL": "water_system_simulator.modeling.hydrology.runoff_models.TOPMODEL",
        "WETSPAModel": "water_system_simulator.modeling.hydrology.runoff_models.WETSPAModel",
        "ShanbeiModel": "water_system_simulator.modeling.hydrology.runoff_models.ShanbeiModel",
        "HebeiModel": "water_system_simulator.modeling.hydrology.runoff_models.HebeiModel",
        # Routing Models
        "MuskingumModel": "water_system_simulator.modeling.hydrology.routing_models.MuskingumModel",
        "UnitHydrographRoutingModel": "water_system_simulator.modeling.hydrology.routing_models.UnitHydrographRoutingModel",
        "LinearReservoirRoutingModel": "water_system_simulator.modeling.hydrology.routing_models.LinearReservoirRoutingModel",
        "VariableVolumeRoutingModel": "water_system_simulator.modeling.hydrology.routing_models.VariableVolumeRoutingModel",
        # Instruments
        "LevelSensor": "water_system_simulator.modeling.instrument_models.LevelSensor",
        "GateActuator": "water_system_simulator.modeling.instrument_models.GateActuator",
    }

    @classmethod
    def get_class(cls, class_name: str):
        """Dynamically imports and returns a class from the registry."""
        if class_name not in cls._CLASS_MAP:
            raise ImportError(f"Component type '{class_name}' not found in registry.")

        full_path = cls._CLASS_MAP[class_name]
        module_path, class_name_only = full_path.rsplit('.', 1)

        try:
            module = importlib.import_module(module_path)
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
        self.datasets: Dict[str, Any] = {}

    def _create_strategy(self, strategy_info: dict):
        """Creates a strategy object from its configuration info."""
        strategy_type = strategy_info["type"]
        strategy_params = strategy_info.get("params", {})
        strategy_class = ComponentRegistry.get_class(strategy_type)
        return strategy_class(**strategy_params)

    def _build_system(self):
        """Constructs the system of components from the configuration."""
        if "components" not in self.config:
            raise ValueError("Configuration must contain a 'components' dictionary.")

        component_configs = self.config["components"]
        for name, comp_info in component_configs.items():
            comp_type = comp_info["type"]
            params = comp_info.get("params", {})

            # Special handling for components that require strategy injection
            if comp_type == "SemiDistributedHydrologyModel":
                strategies_config = params.pop("strategies", None)
                if not strategies_config:
                    raise ValueError("SemiDistributedHydrologyModel requires a 'strategies' config.")

                runoff_strategy = self._create_strategy(strategies_config["runoff"])
                routing_strategy = self._create_strategy(strategies_config["routing"])

                component_class = ComponentRegistry.get_class(comp_type)
                self.components[name] = component_class(
                    runoff_strategy=runoff_strategy,
                    routing_strategy=routing_strategy,
                    **params
                )
            elif comp_type == "RainfallProcessor":
                strategy_config = params.pop("strategy", None)
                if not strategy_config:
                    raise ValueError("RainfallProcessor requires a 'strategy' config.")

                interpolation_strategy = self._create_strategy(strategy_config)

                component_class = ComponentRegistry.get_class(comp_type)
                self.components[name] = component_class(
                    strategy=interpolation_strategy,
                    **params
                )
            else:
                # Default behavior for all other components
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
        self.datasets = config.get("datasets", {})
        self.components = {}
        self._build_system()

        # --- Preprocessing Step ---
        preprocessing_order = self.config.get("preprocessing", [])
        for comp_name in preprocessing_order:
            if comp_name not in self.components:
                raise ValueError(f"Component '{comp_name}' in 'preprocessing' order not found.")
            component = self.components[comp_name]
            if not hasattr(component, 'run_preprocessing'):
                raise TypeError(f"Component '{comp_name}' does not have a 'run_preprocessing' method.")
            component.run_preprocessing(self)

        # --- Simulation Loop ---
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
