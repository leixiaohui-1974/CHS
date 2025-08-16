from __future__ import annotations
from typing import Optional, Dict, Any, TYPE_CHECKING

from .base import BaseAgent
from ..control.pid_controller import PIDController
from ..control.rule_based_controller import RuleBasedOperationalController
from ..control.mpc_controller import MPCController

if TYPE_CHECKING:
    from .communication import MessageBus


class PIDControllerAgent(BaseAgent):
    """
    An agent that encapsulates a PID controller.
    """
    def __init__(self, id: str, message_bus: Optional[MessageBus] = None, **controller_params):
        """
        Initializes the PIDControllerAgent.
        Args:
            id (str): The unique identifier for the agent.
            message_bus (MessageBus, optional): The message bus for communication.
            **controller_params: Parameters for the PIDController.
        """
        super().__init__(id=id, message_bus=message_bus)
        self.controller = PIDController(**controller_params)

    def step(self, dt: float, **kwargs):
        """
        Executes a step of the PID controller.
        Expects 'error_source' in kwargs.
        """
        control_action = self.controller.step(dt, **kwargs)
        # In a real scenario, this action would be sent as a message
        # to an actuator agent.
        return control_action

    def get_state(self) -> Dict[str, Any]:
        """
        Returns the state of the encapsulated controller.
        """
        state = super().get_state()
        state.update(self.controller.get_state())
        return state


class RuleBasedOperationalControllerAgent(BaseAgent):
    """
    An agent that encapsulates a rule-based controller.
    """
    def __init__(self, id: str, message_bus: Optional[MessageBus] = None, **controller_params):
        """
        Initializes the RuleBasedOperationalControllerAgent.
        Args:
            id (str): The unique identifier for the agent.
            message_bus (MessageBus, optional): The message bus for communication.
            **controller_params: Parameters for the RuleBasedOperationalController.
        """
        super().__init__(id=id, message_bus=message_bus)
        self.controller = RuleBasedOperationalController(**controller_params)

    def step(self, dt: float, **kwargs):
        """
        Executes a step of the rule-based controller.
        Expects the current state of the system in kwargs.
        """
        control_action = self.controller.step(dt, **kwargs)
        return control_action

    def get_state(self) -> Dict[str, Any]:
        """
        Returns the state of the encapsulated controller.
        """
        state = super().get_state()
        state.update(self.controller.get_state())
        return state


class MPCControllerAgent(BaseAgent):
    """
    An agent that encapsulates an MPC controller.
    """
    def __init__(self, id: str, message_bus: Optional[MessageBus] = None, **controller_params):
        """
        Initializes the MPCControllerAgent.
        Args:
            id (str): The unique identifier for the agent.
            message_bus (MessageBus, optional): The message bus for communication.
            **controller_params: Parameters for the MPCController.
        """
        super().__init__(id=id, message_bus=message_bus)
        self.controller = MPCController(**controller_params)

    def step(self, dt: float, **kwargs):
        """
        Executes a step of the MPC controller.
        Expects the current state of the system in kwargs.
        """
        control_action = self.controller.step(dt, **kwargs)
        return control_action

    def get_state(self) -> Dict[str, Any]:
        """
        Returns the state of the encapsulated controller.
        """
        state = super().get_state()
        state.update(self.controller.get_state())
        return state
