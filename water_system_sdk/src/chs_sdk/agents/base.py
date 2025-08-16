from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING, Optional

from .agent_status import AgentStatus
from .message import Message
from .fsm import StateMachine, State

if TYPE_CHECKING:
    from ..core.host import AgentKernel


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the CHS platform.
    Now with state machine capabilities.
    """
    def __init__(self, agent_id: str, kernel: 'AgentKernel', **config):
        self.agent_id = agent_id
        self.kernel = kernel
        self.config = config
        self.status: AgentStatus = AgentStatus.INITIALIZING
        self.state_machine: Optional[StateMachine] = None
        self.filter = None

    def setup(self):
        """
        Called once after the agent is initialized.
        Use this for one-time setup tasks.
        """
        pass

    def execute(self, current_time: float, time_step: float):
        """
        The main execution loop for the agent.
        This method delegates execution to the current state of the state machine.
        """
        if self.state_machine:
            self.state_machine.execute(current_time, time_step)

    def on_message(self, message: Message):
        """
        Called by the kernel when the agent receives a message.
        The message is passed to the current state for handling.
        """
        if self.state_machine and hasattr(self.state_machine.current_state, 'on_message'):
            self.state_machine.current_state.on_message(message)

    def transition_to(self, state_name: str):
        """
        A convenience method to transition the agent's state machine to a new state.
        """
        if self.state_machine:
            self.state_machine.transition_to(state_name)

    def shutdown(self):
        """
        Called once when the simulation is shutting down.
        Use this for cleanup tasks.
        """
        pass

    def _assimilate(self, measurement: float):
        """
        Updates the agent's state using a measurement via the Kalman filter.
        """
        if self.filter:
            import numpy as np
            self.filter.update(np.array([measurement]))

    def _publish(self, topic: str, payload: Any):
        """
        A convenience method for publishing a message to the message bus.
        """
        if self.kernel and self.kernel.message_bus:
            message = Message(topic=topic, sender_id=self.agent_id, payload=payload)
            self.kernel.message_bus.publish(message)
