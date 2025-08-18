import pandas as pd
import numpy as np
import importlib
import functools
import logging
import logging.config
from typing import Dict, Any, List, Optional

from chs_sdk.core.simulation_modes import SimulationMode

# --- Helper functions for attribute access ---

def getattr_by_path(obj: Any, path: str) -> Any:
    """
    Access a nested attribute or dictionary key using a dot-separated path.
    Handles the special keyword 'state' by calling the object's get_state() method.
    """
    path_keys = path.split('.')
    current_val = obj

    # Special handling for the 'state' keyword, which is a common convention in this SDK
    if path_keys[0] == 'state':
        if hasattr(current_val, 'get_state') and callable(getattr(current_val, 'get_state')):
            current_val = current_val.get_state()
            path_keys.pop(0) # Remove 'state' from the path to be processed
        else:
            # If there's no get_state() method, it might be a literal attribute named 'state'
            # Proceed with the standard getattr logic below.
            pass

    for key in path_keys:
        if isinstance(current_val, dict):
            try:
                current_val = current_val[key]
            except KeyError:
                raise AttributeError(f"Dictionary does not have key '{key}' in path '{path}'")
        else:
            try:
                current_val = getattr(current_val, key)
            except AttributeError:
                 raise AttributeError(f"Object {current_val} does not have attribute '{key}' in path '{path}'")

    return current_val


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
        "RainfallProcessor": "chs_sdk.preprocessing.rainfall_processor.RainfallProcessor",
        "InverseDistanceWeightingInterpolator": "chs_sdk.preprocessing.interpolators.InverseDistanceWeightingInterpolator",
        "ThiessenPolygonInterpolator": "chs_sdk.preprocessing.interpolators.ThiessenPolygonInterpolator",
        "KrigingInterpolator": "chs_sdk.preprocessing.interpolators.KrigingInterpolator",
        # Controllers
        "PIDController": "chs_sdk.modules.control.pid_controller.PIDController",
        "MPCController": "chs_sdk.modules.control.mpc_controller.MPCController",
        "GainScheduledMPCController": "chs_sdk.modules.control.gs_mpc_controller.GainScheduledMPCController",
        "RuleBasedOperationalController": "chs_sdk.modules.control.rule_based_controller.RuleBasedOperationalController",
        "RecursiveLeastSquaresAgent": "chs_sdk.modules.control.rls_estimator.RecursiveLeastSquaresAgent",
        "ParameterKalmanFilterAgent": "chs_sdk.modules.control.kf_estimator.ParameterKalmanFilterAgent",
        # Disturbances
        "Disturbance": "chs_sdk.modules.disturbances.predefined.Disturbance",
        "TimeSeriesDisturbance": "chs_sdk.modules.disturbances.timeseries_disturbance.TimeSeriesDisturbance",
        "RainfallAgent": "chs_sdk.modules.disturbances.agents.RainfallAgent",
        "DemandAgent": "chs_sdk.modules.disturbances.agents.DemandAgent",
        "PriceAgent": "chs_sdk.modules.disturbances.agents.PriceAgent",
        "FaultAgent": "chs_sdk.modules.disturbances.agents.FaultAgent",
        # --- Entities ---
        "BasePhysicalEntity": "chs_sdk.modules.modeling.base_physical_entity.BasePhysicalEntity",
        "ChannelEntity": "chs_sdk.modules.modeling.entities.channel_entity.ChannelEntity",

        # --- Models ---
        # Hydrodynamic Models
        "SteadyChannelModel": "chs_sdk.modules.modeling.hydrodynamics.channel_models.SteadyChannelModel",
        "StVenantModel": "chs_sdk.modules.modeling.hydrodynamics.channel_models.StVenantModel",

        # Storage / Routing Models
        "ReservoirModel": "chs_sdk.modules.modeling.storage_models.LinearTank",
        "FirstOrderSystem": "chs_sdk.modules.modeling.first_order_system.FirstOrderSystem",
        "MuskingumChannelModel": "chs_sdk.modules.modeling.storage_models.MuskingumChannelModel",
        "FirstOrderInertiaModel": "chs_sdk.modules.modeling.storage_models.FirstOrderInertiaModel",
        "IntegralDelayModel": "chs_sdk.modules.modeling.delay_models.IntegralDelayModel",
        "IntegralPlusDelayModel": "chs_sdk.modules.modeling.integral_plus_delay_model.IntegralPlusDelayModel",
        "PiecewiseIntegralDelayModel": "chs_sdk.modules.modeling.adaptive_models.PiecewiseIntegralDelayModel",
        "GateModel": "chs_sdk.modules.modeling.control_structure_models.SluiceGate",
        "PumpStationModel": "chs_sdk.modules.modeling.control_structure_models.PumpStationModel",
        "TwoDimensionalHydrodynamicModel": "chs_sdk.modules.modeling.two_dimensional_hydrodynamic_model.TwoDimensionalHydrodynamicModel",
        "SemiDistributedHydrologyModel": "chs_sdk.modules.modeling.hydrology.semi_distributed.SemiDistributedHydrologyModel",
        # Runoff Models
        "RunoffCoefficientModel": "chs_sdk.modules.modeling.hydrology.runoff_models.RunoffCoefficientModel",
        "XinanjiangModel": "chs_sdk.modules.modeling.hydrology.runoff_models.XinanjiangModel",
        "SCSRunoffModel": "chs_sdk.modules.modeling.hydrology.runoff_models.SCSRunoffModel",
        "TankModel": "chs_sdk.modules.modeling.hydrology.runoff_models.TankModel",
        "HYMODModel": "chs_sdk.modules.modeling.hydrology.runoff_models.HYMODModel",
        "GreenAmptRunoffModel": "chs_sdk.modules.modeling.hydrology.runoff_models.GreenAmptRunoffModel",
        "TOPMODEL": "chs_sdk.modules.modeling.hydrology.runoff_models.TOPMODEL",
        "WETSPAModel": "chs_sdk.modules.modeling.hydrology.runoff_models.WETSPAModel",
        "ShanbeiModel": "chs_sdk.modules.modeling.hydrology.runoff_models.ShanbeiModel",
        "HebeiModel": "chs_sdk.modules.modeling.hydrology.runoff_models.HebeiModel",
        # Routing Models
        "MuskingumModel": "chs_sdk.modules.modeling.hydrology.routing_models.MuskingumModel",
        "UnitHydrographRoutingModel": "chs_sdk.modules.modeling.hydrology.routing_models.UnitHydrographRoutingModel",
        "LinearReservoirRoutingModel": "chs_sdk.modules.modeling.hydrology.routing_models.LinearReservoirRoutingModel",
        "VariableVolumeRoutingModel": "chs_sdk.modules.modeling.hydrology.routing_models.VariableVolumeRoutingModel",
        # Instruments
        "LevelSensor": "chs_sdk.modules.modeling.instrument_models.LevelSensor",
        "GateActuator": "chs_sdk.modules.modeling.instrument_models.GateActuator",

        # --- Data Processing ---
        "DataSmoother": "chs_sdk.modules.data_processing.processors.DataSmoother",
        "DataFusionEngine": "chs_sdk.modules.data_processing.processors.DataFusionEngine",
        "OutlierRemover": "chs_sdk.modules.data_processing.processors.OutlierRemover",
        "NoiseInjector": "chs_sdk.modules.data_processing.processors.NoiseInjector",

        # --- Custom Agents ---
        "SensorClusterAgent": "chs_sdk.modules.modeling.sensor_cluster_agent.SensorClusterAgent",
        "PumpStationAgent": "chs_sdk.modules.modeling.pump_station_agent.PumpStationAgent",
        "CentralDataFusionAgent": "chs_sdk.modules.modeling.central_data_fusion_agent.CentralDataFusionAgent",

        # --- Body Agents ---
        # "BaseBodyAgent": "chs_sdk.modeling.body_agent.BaseBodyAgent",
        # "ReservoirBodyAgent": "chs_sdk.modeling.body_agent.ReservoirBodyAgent",

        # --- New Agent Architecture ---
        "BaseAgent": "chs_sdk.agent.base_agent.BaseAgent",
        "BaseEmbodiedAgent": "chs_sdk.agent.base_agent.BaseEmbodiedAgent",
        "BaseDisturbanceAgent": "chs_sdk.agent.base_agent.BaseDisturbanceAgent",
        "BodyAgent": "chs_sdk.agent.body_agent.BodyAgent",
        "ControlAgent": "chs_sdk.agent.control_agent.ControlAgent",
        "PerceptionAgent": "chs_sdk.agent.perception_agent.PerceptionAgent",
        "DispatchAgent": "chs_sdk.agent.dispatch_agent.DispatchAgent",
        "CentralManagementAgent": "chs_sdk.agent.central_management_agent.CentralManagementAgent",
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
    """Manages the setup and execution of water system simulations.

    This class is the main entry point for running simulations. It is responsible
    for parsing a configuration dictionary, building a system of interconnected
    components, executing the simulation loop, and returning the results.

    The manager itself is stateless between runs, meaning a single instance can be
    used to run multiple different simulations, each with its own configuration.

    Attributes:
        components (Dict[str, Any]): A dictionary of all component instances
            in the current simulation, keyed by their names.
        config (Dict[str, Any]): The configuration dictionary for the current
            simulation.
        datasets (Dict[str, Any]): A dictionary to hold any datasets loaded
            during preprocessing, for access by components during the simulation.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initializes the simulation manager."""
        self.components: Dict[str, Any] = {}
        self.config: Dict[str, Any] = {}
        self.datasets: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)

        # New attributes for step-by-step execution
        self._time_steps: np.ndarray = np.array([])
        self._current_step_index: int = 0
        self._is_initialized: bool = False
        self._is_finished: bool = False
        self.history: List[Dict[str, Any]] = []
        self.current_results: Dict[str, Any] = {}
        self.dt: float = 1.0

        if config:
            self.load_config(config)
            self.initialize()

    @property
    def t(self) -> float:
        """Returns the current simulation time."""
        if self._is_initialized and not self._is_finished:
            return self._time_steps[self._current_step_index]
        return 0.0

    def _create_strategy(self, strategy_info: dict):
        """Creates a strategy object from its configuration info."""
        strategy_type = strategy_info["type"]
        strategy_params = strategy_info.get("params", {})
        strategy_class = ComponentRegistry.get_class(strategy_type)
        return strategy_class(**strategy_params)

    def _create_pipeline(self, pipeline_config: dict):
        """Creates a DataProcessingPipeline from its configuration."""
        from chs_sdk.data_processing.pipeline import DataProcessingPipeline

        processor_instances = []
        processor_configs = pipeline_config.get("processors", [])
        for proc_config in processor_configs:
            proc_type = proc_config["type"]
            proc_params = proc_config.get("params", {})
            proc_class = ComponentRegistry.get_class(proc_type)
            processor_instances.append(proc_class(**proc_params))

        return DataProcessingPipeline(processors=processor_instances)

    def _create_model_instance(self, model_config: Optional[Dict[str, Any]]):
        """Creates a model instance from its configuration dictionary."""
        if not model_config:
            return None
        model_type = model_config["type"]
        model_params = model_config.get("properties", {}) # Use 'properties' to match YAML
        model_class = ComponentRegistry.get_class(model_type)
        return model_class(**model_params)

    def _build_system(self):
        """Constructs the system of components from the configuration."""
        if "components" not in self.config:
            raise ValueError("Configuration must contain a 'components' dictionary.")

        component_configs = self.config["components"]
        for name, comp_info in component_configs.items():
            comp_type = comp_info["type"]
            # Handle both 'properties' and 'params' for component configuration
            if 'properties' in comp_info:
                params = comp_info.get("properties", {})
            else:
                params = comp_info.get("params", {})

            # --- Determine Component Type ---
            component_class = ComponentRegistry.get_class(comp_type)
            is_physical_entity = any(k in comp_info for k in ["steady_model", "dynamic_model", "precision_model"])
            try:
                base_embodied_agent_class = ComponentRegistry.get_class("BaseEmbodiedAgent")
                is_embodied_agent = issubclass(component_class, base_embodied_agent_class)
            except (ImportError, TypeError):
                is_embodied_agent = False

            # --- Build Component Based on Type ---
            if is_physical_entity:
                # Instantiate the three models
                steady_model = self._create_model_instance(comp_info.get("steady_model"))
                dynamic_model = self._create_model_instance(comp_info.get("dynamic_model"))
                precision_model = self._create_model_instance(comp_info.get("precision_model"))

                # Entity-level params are those not related to model definitions
                entity_params = params.copy()
                entity_params['name'] = name

                self.components[name] = component_class(
                    steady_model=steady_model,
                    dynamic_model=dynamic_model,
                    precision_model=precision_model,
                    **entity_params
                )

            elif "dynamic_model_bank" in comp_info:
                # Pass entity-level params, but exclude model bank config
                entity_params = {k: v for k, v in comp_info.items() if k not in ["type", "dynamic_model_bank", "initial_active_model"]}
                entity = component_class(**entity_params)

                # Build the model bank
                for model_config in comp_info["dynamic_model_bank"]:
                    model_id = model_config["id"]
                    model_type = model_config["type"]
                    model_params = model_config.get("params", {})
                    model_instance = ComponentRegistry.get_class(model_type)(**model_params)
                    entity.dynamic_model_bank[model_id] = model_instance

                # Set the initial active model
                initial_model_id = comp_info.get("initial_active_model")
                if not initial_model_id:
                    raise ValueError(f"Component '{name}' has a model bank but no 'initial_active_model' set.")
                if initial_model_id not in entity.dynamic_model_bank:
                    raise ValueError(f"Initial model '{initial_model_id}' not found in the model bank for '{name}'.")
                entity.active_dynamic_model_id = initial_model_id
                self.components[name] = entity

            elif is_embodied_agent:
                # Build core_physics_model
                core_physics_model_config = params.pop("core_physics_model")
                core_physics_model = self._create_model_instance(core_physics_model_config)

                # Build sensors
                sensors = {}
                sensors_config = params.pop("sensors", {})
                for sensor_name, sensor_config in sensors_config.items():
                    sensor_class = ComponentRegistry.get_class(sensor_config["type"])
                    sensor_params = sensor_config.get("params", {})
                    if "pipeline" in sensor_params:
                        pipeline_config = sensor_params.pop("pipeline")
                        sensor_params["pipeline"] = self._create_pipeline(pipeline_config)
                    sensors[sensor_name] = sensor_class(**sensor_params)

                # Build actuators
                actuators = {}
                actuators_config = params.pop("actuators", {})
                for actuator_name, actuator_config in actuators_config.items():
                    actuator_class = ComponentRegistry.get_class(actuator_config["type"])
                    actuator_params = actuator_config.get("params", {})
                    actuators[actuator_name] = actuator_class(**actuator_params)

                # Create the body agent
                self.components[name] = component_class(
                    core_physics_model=core_physics_model,
                    sensors=sensors,
                    actuators=actuators,
                    **params # remaining params
                )

            elif comp_type == "SemiDistributedHydrologyModel":
                strategies_config = params.pop("strategies", None)
                if not strategies_config:
                    raise ValueError("SemiDistributedHydrologyModel requires a 'strategies' config.")
                runoff_strategy = self._create_strategy(strategies_config["runoff"])
                routing_strategy = self._create_strategy(strategies_config["routing"])
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
                self.components[name] = component_class(
                    strategy=interpolation_strategy,
                    **params
                )

            else:
                # Default behavior for all other components
                if "pipeline" in params:
                    pipeline_config = params.pop("pipeline")
                    params["pipeline"] = self._create_pipeline(pipeline_config)
                self.components[name] = component_class(**params)

    def _execute_step(self, instruction: Any, t: float, dt: float, simulation_mode: SimulationMode):
        """Executes a single instruction from the execution_order."""
        if isinstance(instruction, str):
            # It's a simple component name, call the standard step method
            component = self.components[instruction]
            # Pass simulation_mode to entities, otherwise call standard step
            if isinstance(component, ComponentRegistry.get_class("BasePhysicalEntity")):
                 component.step(simulation_mode=simulation_mode, dt=dt, t=t)
            else:
                 component.step(dt=dt, t=t)

        elif isinstance(instruction, dict):
            # It's a detailed instruction for a method call
            comp_name = instruction["component"]
            method_name = instruction["method"]

            # Resolve potentially nested component path
            try:
                component = getattr_by_path(self, f"components.{comp_name}")
            except AttributeError:
                raise AttributeError(f"Component '{comp_name}' not found in simulation components.")

            # Prepare arguments for the method call
            args = {}
            # Add simulation_mode to args if the method is 'step' and the component is an entity
            if method_name == 'step' and isinstance(component, ComponentRegistry.get_class("BasePhysicalEntity")):
                args['simulation_mode'] = simulation_mode

            for arg_name, source_path in instruction.get("args", {}).items():
                if source_path == "simulation.dt":
                    args[arg_name] = dt
                elif source_path == "simulation.t":
                    args[arg_name] = t
                elif source_path == "simulation.system_state":
                    args[arg_name] = self.components
                else:
                    # If the source path contains a dot, treat it as a reference to another component's attribute.
                    # Otherwise, treat it as a literal value.
                    if isinstance(source_path, str) and '.' in source_path:
                        source_comp, source_attr = source_path.split('.', 1)
                        args[arg_name] = getattr_by_path(self.components[source_comp], source_attr)
                    else:
                        args[arg_name] = source_path

            # Get the method
            method = getattr(component, method_name)

            # Call the method
            result = method(**args)

            # Store the result if a destination is specified
            if "result_to" in instruction and result is not None:
                target_comp, target_attr = instruction["result_to"].split('.', 1)
                setattr_by_path(self.components[target_comp], target_attr, result)  # type: ignore
        else:
            raise TypeError(f"Unsupported instruction type in execution_order: {type(instruction)}")

    def _check_and_execute_events(self, t: float):
        """Checks and executes events based on triggers."""
        events = self.config.get("events", [])
        for event in events:
            trigger = event["trigger"]
            action = event["action"]

            triggered = False
            if trigger["type"] == "condition":
                # Example: "upstream_inflow.state.value > 1000.0"
                condition_str = trigger["value"]
                # A simple, unsafe eval. For a real product, a safe expression parser is needed.
                # We create a local context for the eval with component names and the simulation manager itself.
                local_context = {name: comp for name, comp in self.components.items()}
                local_context['simulation'] = self
                self._current_t = t # Store t for access via simulation.t
                try:
                    if eval(condition_str, {"__builtins__": {}}, local_context):
                        triggered = True
                except Exception as e:
                    self.logger.warning(f"Could not evaluate trigger condition '{condition_str}' at time {t}. Error: {e}")

            elif trigger["type"] == "always":
                triggered = True

            if triggered:
                action_type = action["type"]
                if action_type == "switch_model":
                    target_entity_name = action["target"]
                    new_model_id = action["value"]

                    if target_entity_name not in self.components:
                        self.logger.warning(f"Could not switch model. Target entity '{target_entity_name}' not found.")
                        continue

                    target_entity = self.components[target_entity_name]

                    if not hasattr(target_entity, 'dynamic_model_bank'):
                        self.logger.warning(f"Could not switch model. Target '{target_entity_name}' is not a physical entity with a model bank.")
                        continue

                    if new_model_id not in target_entity.dynamic_model_bank:
                        self.logger.warning(f"Could not switch model. Model ID '{new_model_id}' not found in bank for '{target_entity_name}'.")
                        continue

                    target_entity.active_dynamic_model_id = new_model_id

                elif action_type == "set_param":
                    target_path = action["target"]

                    # Determine the value to be set
                    if "value_from" in action:
                        source_path = action["value_from"]
                        try:
                            value = getattr_by_path(self, f"components.{source_path}")
                        except AttributeError as e:
                            self.logger.warning(e)
                            continue
                    else:
                        value = action["value"]

                    # Set the parameter using the potentially new syntax
                    try:
                        # Check for model bank syntax: entity::model.param
                        if "::" in target_path:
                            entity_name, model_path = target_path.split("::", 1)
                            model_id, param_path = model_path.split(".", 1)

                            if entity_name not in self.components:
                                raise AttributeError(f"Target entity '{entity_name}' not found.")

                            entity = self.components[entity_name]
                            if not hasattr(entity, 'dynamic_model_bank') or model_id not in entity.dynamic_model_bank:
                                raise AttributeError(f"Model '{model_id}' not found in entity '{entity_name}'.")

                            target_model = entity.dynamic_model_bank[model_id]
                            setattr_by_path(target_model, param_path, value)

                        else:
                            # Standard component parameter
                            setattr_by_path(self, f"components.{target_path}", value)

                    except (AttributeError, ValueError) as e:
                        self.logger.warning(f"Could not set parameter for target '{target_path}'. Error: {e}")
                        continue

    def _setup_logging(self) -> None:
        """Configures logging for the simulation."""
        log_config = self.config.get("logging")
        if log_config and isinstance(log_config, dict):
            try:
                logging.config.dictConfig(log_config)
                self.logger.info("Logging configured from dictionary.")
            except (ValueError, TypeError, AttributeError, ImportError) as e:
                logging.basicConfig(level=logging.WARNING)
                self.logger.warning(f"Failed to configure logging from dictConfig: {e}. Falling back to basic config.")
        else:
            # Default basic configuration if no config is provided or it's invalid
            logging.basicConfig(level=logging.INFO,
                                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            self.logger.info("Using default basic logging configuration because no valid 'logging' section was found in config.")

    def load_config(self, config: Dict[str, Any]):
        """Loads a configuration and builds the system."""
        # Reset state for the new run
        self.config = self._preprocess_config(config)
        self._setup_logging()
        self.datasets = self.config.get("datasets", {})
        self.components = {}
        self._build_system()

    def _preprocess_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Pre-processes the raw config to a standard format."""
        # This handles the case where 'components' is a list from YAML
        if isinstance(config.get("components"), list):
            processed_config = config.copy()
            components_dict = {comp['name']: comp for comp in config['components']}
            processed_config['components'] = components_dict
            return processed_config
        return config

    def initialize(self, mode: str = "DYNAMIC", **kwargs):
        """
        Initializes the simulation environment, builds components, and sets up
        the time steps for the run.
        """
        if not self.config:
            raise RuntimeError("Configuration must be loaded before initializing.")

        self.simulation_mode = SimulationMode[mode.upper()]

        # --- Preprocessing Step ---
        preprocessing_order = self.config.get("preprocessing", [])
        for comp_name in preprocessing_order:
            if comp_name not in self.components:
                raise ValueError(f"Component '{comp_name}' in 'preprocessing' order not found.")
            component = self.components[comp_name]
            if not hasattr(component, 'run_preprocessing'):
                raise TypeError(f"Component '{comp_name}' does not have a 'run_preprocessing' method.")
            component.run_preprocessing(self)

        # --- Setup Simulation Loop ---
        sim_params = self.config.get("simulation_params", {})
        total_time = kwargs.get('total_time', sim_params.get("total_time", 100))
        self.dt = kwargs.get('dt', sim_params.get("dt", 1.0))

        if self.simulation_mode == SimulationMode.STEADY:
            self._time_steps = np.array([0.0])
        else:
            self._time_steps = np.arange(0, total_time, self.dt)

        self._is_initialized = True
        self._is_finished = False
        self._current_step_index = 0
        self.history = []

    def run_step(self) -> None:
        """Executes a single step of the simulation."""
        if not self._is_initialized or self._is_finished:
            self.logger.warning("run_step called on uninitialized or finished simulation.")
            return

        t = self._time_steps[self._current_step_index]
        connections = self.config.get("connections", [])
        execution_order = self.config.get("execution_order", [])
        logger_config = self.config.get("logger_config", [])

        # 1. Check and execute events
        self._check_and_execute_events(t)

        # 2. Process connections
        for conn in connections:
            source_comp_name, source_attr_path = conn["source"].split('.', 1)
            target_comp_name, target_attr_path = conn["target"].split('.', 1)
            value = getattr_by_path(self.components[source_comp_name], source_attr_path)
            setattr_by_path(self.components[target_comp_name], target_attr_path, value)

        # 3. Execute components
        for instruction in execution_order:
            self._execute_step(instruction, t=t, dt=self.dt, simulation_mode=self.simulation_mode)

        # 4. Log data
        step_log = {"time": t}
        for log_path in logger_config:
            comp_name, attr_path = log_path.split('.', 1)
            value = getattr_by_path(self.components[comp_name], attr_path)
            step_log[log_path] = value
        self.history.append(step_log)
        self.current_results = step_log

        # 5. Advance step counter
        self._current_step_index += 1
        if self._current_step_index >= len(self._time_steps):
            self._is_finished = True

    def is_running(self) -> bool:
        """Returns True if the simulation is initialized and has more steps to run."""
        return self._is_initialized and not self._is_finished

    def get_results(self) -> pd.DataFrame:
        """Returns the simulation results up to the current step as a DataFrame."""
        return pd.DataFrame(self.history)

    def run(self, mode: str = "DYNAMIC", **kwargs) -> pd.DataFrame:
        """Runs a complete simulation based on the loaded configuration."""
        self.initialize(mode, **kwargs)
        while self.is_running():
            self.run_step()
        return self.get_results()
