from __future__ import annotations
from typing import Optional, Dict, Any, TYPE_CHECKING

from .base import BaseDisturbanceAgent
from ..disturbances.disturbance_models import RainfallModel, WaterConsumptionModel

if TYPE_CHECKING:
    from .communication import MessageBus


class RainfallAgent(BaseDisturbanceAgent):
    """
    An agent that introduces rainfall into the system.
    """
    def __init__(self, id: str, message_bus: Optional[MessageBus] = None, **model_params):
        """
        Initializes the RainfallAgent.
        Args:
            id (str): The unique identifier for the agent.
            message_bus (MessageBus, optional): The message bus for communication.
            **model_params: Parameters for the RainfallModel.
        """
        super().__init__(id=id, message_bus=message_bus)
        self.rainfall_model = RainfallModel(**model_params)
        self.time_step = 0

    def step(self, dt: float, **kwargs):
        """
        Gets the rainfall for the current time step and sends it as a message.
        """
        rainfall = self.rainfall_model.get_rainfall(self.time_step)
        self.time_step += 1
        # In a real scenario, this would send a message to a target agent,
        # e.g., a catchment or reservoir agent.
        return rainfall

    def get_state(self) -> Dict[str, Any]:
        """
        Returns the current state of the rainfall agent.
        """
        state = super().get_state()
        state["time_step"] = self.time_step
        return state


class WaterConsumptionAgent(BaseDisturbanceAgent):
    """
    An agent that represents water consumption from the system.
    """
    def __init__(self, id: str, message_bus: Optional[MessageBus] = None, **model_params):
        """
        Initializes the WaterConsumptionAgent.
        Args:
            id (str): The unique identifier for the agent.
            message_bus (MessageBus, optional): The message bus for communication.
            **model_params: Parameters for the WaterConsumptionModel.
        """
        super().__init__(id=id, message_bus=message_bus)
        self.consumption_model = WaterConsumptionModel(**model_params)
        self.time_step = 0

    def step(self, dt: float, **kwargs):
        """
        Gets the consumption for the current time step and sends it as a message.
        """
        consumption = self.consumption_model.get_consumption(self.time_step)
        self.time_step += 1
        # This would typically be sent as a message to a reservoir or offtake node.
        return consumption

    def get_state(self) -> Dict[str, Any]:
        """
        Returns the current state of the consumption agent.
        """
        state = super().get_state()
        state["time_step"] = self.time_step
        return state
