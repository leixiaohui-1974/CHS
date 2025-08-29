from typing import Dict, Any, List

class SimulationBuilder:
    """
    A builder class for programmatically constructing simulation configurations.

    This class provides a more intuitive and safer way to create the
    configuration dictionary required by the SimulationManager, using a
    fluent interface.

    Example:
        builder = SimulationBuilder()
        config = (builder
                  .set_simulation_params(total_time=1000, dt=1.0)
                  .add_component("reservoir", "ReservoirModel", {"area": 100})
                  .add_connection("reservoir.state.level", "controller.input.value")
                  .build())
    """
    def __init__(self):
        self._config: Dict[str, Any] = {
            "simulation_params": {},
            "components": {},
            "connections": [],
            "execution_order": [],
            "logger_config": []
        }

    def set_simulation_params(self, total_time: int, dt: float) -> 'SimulationBuilder':
        """Sets the core simulation time parameters."""
        self._config["simulation_params"] = {"total_time": total_time, "dt": dt}
        return self

    def add_component(self, name: str, component_type: str, params: Dict[str, Any]) -> 'SimulationBuilder':
        """
        Adds a component (e.g., a model, a controller) to the simulation.

        Args:
            name: A unique name for the component instance.
            component_type: The class name of the component to instantiate.
            params: A dictionary of parameters to initialize the component.
        """
        self._config["components"][name] = {"type": component_type, "params": params}
        return self

    def add_connection(self, source: str, target: str) -> 'SimulationBuilder':
        """
        Adds a data-flow connection between components.

        Args:
            source: The source of the data (e.g., "component_name.state.level").
            target: The destination of the data (e.g., "other_component.input.inflow").
        """
        self._config["connections"].append({"source": source, "target": target})
        return self

    def set_execution_order(self, order: List[str]) -> 'SimulationBuilder':
        """
        Sets the execution order of the components for each simulation step.

        Args:
            order: A list of component names in the desired order of execution.
        """
        self._config["execution_order"] = order
        return self

    def configure_logger(self, logs_to_capture: List[str]) -> 'SimulationBuilder':
        """
        Configures which component attributes to log during the simulation.

        Args:
            logs_to_capture: A list of attributes to log (e.g., "component_name.state.level").
        """
        self._config["logger_config"] = logs_to_capture
        return self

    def build(self) -> Dict[str, Any]:
        """
        Builds and returns the final configuration dictionary.

        This dictionary can be passed directly to the SimulationManager.
        In the future, this method can also be used to validate the configuration.
        """
        return self._config
