from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from .base import EmbodiedAgent
from ..modeling.storage_models import LinearTank, NonlinearTank, MuskingumChannelModel
from ..modeling.station_models import PumpingStation
from ..modeling.pipeline_model import PipelineModel


if TYPE_CHECKING:
    from .communication import MessageBus


class LinearTankAgent(EmbodiedAgent):
    """
    An agent representing a tank or reservoir with a linear level-volume relationship.
    """
    def __init__(self, id: str, message_bus: Optional[MessageBus] = None, **model_params):
        """
        Initializes the LinearTankAgent.
        Args:
            id (str): The unique identifier for the agent.
            message_bus (MessageBus, optional): The message bus for communication.
            **model_params: Parameters for the LinearTank model, e.g., 'area', 'initial_level'.
        """
        core_model = LinearTank(id=f"{id}_model", **model_params)
        super().__init__(id=id, message_bus=message_bus, core_model=core_model)


class NonlinearTankAgent(EmbodiedAgent):
    """
    An agent representing a tank or reservoir with a nonlinear level-volume relationship.
    """
    def __init__(self, id: str, message_bus: Optional[MessageBus] = None, **model_params):
        """
        Initializes the NonlinearTankAgent.
        Args:
            id (str): The unique identifier for the agent.
            message_bus (MessageBus, optional): The message bus for communication.
            **model_params: Parameters for the NonlinearTank model, e.g., 'level_to_volume', 'initial_level'.
        """
        core_model = NonlinearTank(id=f"{id}_model", **model_params)
        super().__init__(id=id, message_bus=message_bus, core_model=core_model)


class MuskingumChannelAgent(EmbodiedAgent):
    """
    An agent representing a channel reach using the Muskingum routing model.
    """
    def __init__(self, id: str, message_bus: Optional[MessageBus] = None, **model_params):
        """
        Initializes the MuskingumChannelAgent.
        Args:
            id (str): The unique identifier for the agent.
            message_bus (MessageBus, optional): The message bus for communication.
            **model_params: Parameters for the MuskingumChannelModel, e.g., 'K', 'x', 'dt'.
        """
        core_model = MuskingumChannelModel(id=f"{id}_model", **model_params)
        super().__init__(id=id, message_bus=message_bus, core_model=core_model)


class PumpingStationAgent(EmbodiedAgent):
    """
    An agent representing a pump station.
    """
    def __init__(self, id: str, message_bus: Optional[MessageBus] = None, **model_params):
        """
        Initializes the PumpingStationAgent.
        Args:
            id (str): The unique identifier for the agent.
            message_bus (MessageBus, optional): The message bus for communication.
            **model_params: Parameters for the PumpingStation model.
        """
        core_model = PumpingStation(id=f"{id}_model", **model_params)
        super().__init__(id=id, message_bus=message_bus, core_model=core_model)

class PipelineAgent(EmbodiedAgent):
    """
    An agent representing a pipe.
    """
    def __init__(self, id: str, message_bus: Optional[MessageBus] = None, **model_params):
        """
        Initializes the PipelineAgent.
        Args:
            id (str): The unique identifier for the agent.
            message_bus (MessageBus, optional): The message bus for communication.
            **model_params: Parameters for the Pipeline model.
        """
        core_model = PipelineModel(id=f"{id}_model", **model_params)
        super().__init__(id=id, message_bus=message_bus, core_model=core_model)
