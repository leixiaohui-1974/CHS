from typing import Dict, Any
from .base_model import BaseModel
from ..core.datastructures import Input

class BaseBodyAgent(BaseModel):
    """
    A generic, composable "Body Agent" that serves as a container for a core
    physics model, sensors, and actuators. It represents a complete physical
    entity in the simulation.
    """

    def __init__(self,
                 core_physics_model: BaseModel,
                 sensors: Dict[str, BaseModel],
                 actuators: Dict[str, BaseModel],
                 **kwargs):
        """
        Initializes the Body Agent.

        Args:
            core_physics_model: An instance of a core physics model (e.g., ReservoirModel).
            sensors: A dictionary of sensor instances, keyed by name.
            actuators: A dictionary of actuator instances, keyed by name.
        """
        super().__init__(**kwargs)
        self.core_physics_model = core_physics_model
        self.sensors = sensors
        self.actuators = actuators

        # This input object will hold commands for the actuators.
        # The keys are expected to be in the format '{actuator_name}_command'.
        self.input = Input()

    def step(self, dt: float, **kwargs):
        """
        This step method is a placeholder. The primary orchestration of the
        body agent's sub-components (actuators, model, sensors) is intended
        to be handled by the SimulationManager's 'execution_order' and
        'connections' configuration. This allows for maximum flexibility in
        defining the data flow and execution sequence.
        """
        # The detailed orchestration is deferred to the SimulationManager config.
        # This method could be used for agent-level logic if needed in the future.
        pass

    def get_state(self) -> Dict[str, Any]:
        """
        Aggregates the state from all sensors into a single dictionary.
        This provides the external "view" of the body agent's perceived state.
        The keys of the dictionary are the names of the sensors.
        """
        aggregated_state = {}
        for name, sensor in self.sensors.items():
            # The value is the sensor's primary output.
            # This simplifies connections from other components.
            aggregated_state[name] = sensor.output
        return aggregated_state

class ReservoirBodyAgent(BaseBodyAgent):
    """
    A concrete implementation of a Body Agent for a reservoir.
    This class is primarily a container and relies on the BaseBodyAgent's
    structure and the SimulationManager's configuration for its behavior.
    """
    def __init__(self, core_physics_model: BaseModel, sensors: Dict[str, BaseModel], actuators: Dict[str, BaseModel], **kwargs):
        super().__init__(core_physics_model=core_physics_model, sensors=sensors, actuators=actuators, **kwargs)
