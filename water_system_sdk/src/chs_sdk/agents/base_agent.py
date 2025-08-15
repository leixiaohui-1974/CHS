from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

from .agent_status import AgentStatus
from .message import Message

if TYPE_CHECKING:
    from .agent_kernel import AgentKernel


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the CHS platform.
    """
    def __init__(self, agent_id: str, kernel: 'AgentKernel', **config):
        self.agent_id = agent_id
        self.kernel = kernel
        self.config = config
        self.status: AgentStatus = AgentStatus.INITIALIZING

    def setup(self):
        """
        Called once after the agent is initialized.
        Use this for one-time setup tasks.
        """
        pass

    @abstractmethod
    def execute(self, current_time: float):
        """
        The main execution loop for the agent.
        This method is called by the kernel at each time step.
        """
        pass

    @abstractmethod
    def on_message(self, message: Message):
        """
        Called by the kernel when the agent receives a message.
        """
        pass

    def shutdown(self):
        """
        Called once when the simulation is shutting down.
        Use this for cleanup tasks.
        """
        pass

    def _publish(self, topic: str, payload: Any):
        """
        A convenience method for publishing a message to the message bus.
        """
        if self.kernel and self.kernel.message_bus:
            message = Message(topic=topic, sender_id=self.agent_id, payload=payload)
            self.kernel.message_bus.publish(message)
