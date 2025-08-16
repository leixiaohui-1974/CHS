from __future__ import annotations
from typing import Dict, Any, Optional, TYPE_CHECKING

from ..modeling.base_model import BaseModel
from ..core.datastructures import Input
from ..data_processing.pipeline import DataProcessingPipeline

if TYPE_CHECKING:
    from .communication import MessageBus


class BaseAgent(BaseModel):
    """
    The ultimate parent class for all agents in the simulation framework.
    It establishes the basic agent identity, interface, and communication ability.
    """
    def __init__(self, id: str, message_bus: Optional[MessageBus] = None, **kwargs):
        super().__init__(id=id, **kwargs)
        self.id = id
        self.message_bus = message_bus
        self.processing_pipeline: Optional[DataProcessingPipeline] = kwargs.get("processing_pipeline")
        self.mode: str = kwargs.get("mode", "dynamic")

    def set_mode(self, new_mode: str):
        """
        Sets the operational mode of the agent.
        """
        if new_mode not in ["dynamic", "steady_state", "transient"]:
            raise ValueError(f"Invalid mode: {new_mode}")
        self.mode = new_mode

    def step(self, dt: float, **kwargs):
        """
        The main method for an agent to perform its actions during a simulation step.
        """
        raise NotImplementedError("Each agent must implement its own step method.")

    def get_state(self) -> Dict[str, Any]:
        """
        Returns the current state of the agent.
        """
        return {"id": self.id, "class": self.__class__.__name__}


class BaseEmbodiedAgent(BaseAgent):
    """
    An abstract base class for agents that have a "physical" presence or are
    directly tied to a simulated physical entity. This includes agents that

    It holds the three core elements that define a physical entity:
    - A physics model for its behavior.
    - Sensors for perception.
    - Actuators for action.
    """
    core_physics_model: Optional[BaseModel] = None
    sensors: Dict[str, BaseModel] = {}
    actuators: Dict[str, BaseModel] = {}

class EmbodiedAgent(BaseEmbodiedAgent):
    """
    A concrete implementation for agents with a physical presence.
    This class provides the basic structure for managing a core physics model.
    """
    def __init__(self, id: str, message_bus: Optional[MessageBus] = None, core_model: Optional[BaseModel] = None, **kwargs):
        super().__init__(id=id, message_bus=message_bus, **kwargs)
        self.core_physics_model = core_model

    def step(self, dt: float, **kwargs):
        """
        Drives the step of the core physics model.
        Inputs for the model are expected to be passed via kwargs, potentially
        from messages received by a more specialized agent.
        """
        if self.core_physics_model:
            model_input = self.prepare_inputs(**kwargs)
            self.core_physics_model.step(dt, **model_input)

    def prepare_inputs(self, **kwargs) -> Dict[str, Any]:
        """
        Prepares the input dictionary for the physics model.
        This base implementation simply passes through inputs from the step kwargs.
        """
        return kwargs.get("inputs", {})

    def get_state(self) -> Dict[str, Any]:
        """
        Returns the state of the core physics model, if it exists.
        """
        state = super().get_state()
        if self.core_physics_model and hasattr(self.core_physics_model, 'get_state'):
            state.update(self.core_physics_model.get_state())
        return state

class BaseDisturbanceAgent(BaseAgent):
    """
    An abstract base class for agents that introduce external or internal
    disturbances into the system, such as faults, changing demands, or
    environmental events like rainfall.
    """
    pass

class CentralManagementAgent(BaseAgent):
    """
    An abstract base class for the "brains" of the operation. This agent is
    responsible for higher-level strategic planning, global state monitoring,
    and coordinating the actions of other agents across the system.
    """
    pass
