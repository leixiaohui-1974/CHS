from abc import ABC
from .base_model import BaseModel

from ..core.datastructures import Input

class BasePhysicalEntity(BaseModel, ABC):
    """
    An abstract base class for physical entities that can manage a bank of
    dynamic models and switch between them during a simulation.
    """
    def __init__(self, **kwargs):
        """
        Initializes the BasePhysicalEntity.

        Args:
            **kwargs: Keyword arguments.
        """
        super().__init__(**kwargs)
        self.dynamic_model_bank = {}
        self.active_dynamic_model_id = None
        self.input = Input() # An entity can have its own inputs
        self.output = None

    def step(self, dt: float, t: float):
        """
        Executes a time step by delegating the call to the currently active
        dynamic model. It is the responsibility of the concrete entity
        to correctly route inputs to the active model.

        Args:
            dt (float): The time step duration.
            t (float): The current simulation time.
        """
        if not self.active_dynamic_model_id:
            raise ValueError("No active dynamic model is set.")

        if self.active_dynamic_model_id not in self.dynamic_model_bank:
            raise ValueError(f"Active model '{self.active_dynamic_model_id}' not found in model bank.")

        active_model = self.dynamic_model_bank[self.active_dynamic_model_id]

        # The concrete entity's step should handle input mapping
        active_model.step(dt=dt, t=t)

        # The entity should also update its own output, typically from the active model
        self.output = active_model.output

    def get_state(self):
        """
        Returns the combined state of the entity and its active model.
        """
        # Start with the entity's own state
        state = super().get_state()
        # Add the state of the active model, prefixed for clarity
        if self.active_dynamic_model_id and self.active_dynamic_model_id in self.dynamic_model_bank:
            active_model = self.dynamic_model_bank[self.active_dynamic_model_id]
            model_state = active_model.get_state()
            for key, value in model_state.items():
                state[f"active_model.{key}"] = value
        return state
