from __future__ import annotations
from typing import Dict, Any
from ..modeling.base_model import BaseModel
from ..core.datastructures import Input

class BaseAgent(BaseModel):
    """
    The ultimate parent class for all agents in the simulation framework.
    It establishes the basic agent identity and interface.
    """
    def step(self, dt: float, **kwargs):
        """
        The main method for an agent to perform its actions during a simulation step.
        """
        raise NotImplementedError("Each agent must implement its own step method.")

    def get_state(self) -> Dict[str, Any]:
        """
        Returns the current state of the agent.
        """
        return {}

class BaseEmbodiedAgent(BaseAgent):
    """
    An abstract base class for agents that have a "physical" presence or are
    directly tied to a simulated physical entity. This includes agents that
    simulate the physical world (BodySimulationAgent) and agents that perceive
    or act upon it (Sensing/ControlEmbodiedAgent).

    It holds the three core elements that define a physical entity:
    - A physics model for its behavior.
    - Sensors for perception.
    - Actuators for action.
    """
    core_physics_model: BaseModel | None = None
    sensors: Dict[str, BaseModel] = {}
    actuators: Dict[str, BaseModel] = {}

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
