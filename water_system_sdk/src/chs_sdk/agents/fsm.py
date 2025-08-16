from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from .base import BaseAgent


class State(ABC):
    """
    Abstract base class for a state in a finite state machine.
    """
    def __init__(self, agent: BaseAgent):
        self._agent = agent

    @property
    def agent(self) -> BaseAgent:
        return self._agent

    def on_enter(self):
        """
        Called when entering this state.
        """
        pass

    @abstractmethod
    def execute(self, current_time: float, time_step: float):
        """
        Called on each time step while in this state.
        """
        pass

    def on_message(self, message):
        """
        Handles incoming messages.
        This method can be overridden by concrete states.
        """
        pass

    def on_exit(self):
        """
        Called when exiting this state.
        """
        pass

    def __repr__(self):
        return self.__class__.__name__


class StateMachine:
    """
    Manages states and transitions for an agent.
    """
    def __init__(self, initial_state: State):
        self._states: Dict[str, State] = {}
        self._current_state: Optional[State] = None
        if initial_state:
            self.add_state(initial_state)
            self._current_state = initial_state
            initial_state.on_enter()

    @property
    def current_state(self) -> Optional[State]:
        return self._current_state

    def add_state(self, state: State):
        """
        Adds a state to the machine.
        """
        self._states[state.__class__.__name__] = state

    def transition_to(self, state_name: str):
        """
        Transitions to a new state.
        """
        if self._current_state and self._current_state.__class__.__name__ == state_name:
            return

        new_state = self._states.get(state_name)
        if not new_state:
            raise ValueError(f"State '{state_name}' not found in state machine.")

        if self._current_state:
            self._current_state.on_exit()

        self._current_state = new_state
        self._current_state.on_enter()

    def execute(self, current_time: float, time_step: float):
        """
        Executes the current state's logic.
        """
        if self._current_state:
            self._current_state.execute(current_time, time_step)
