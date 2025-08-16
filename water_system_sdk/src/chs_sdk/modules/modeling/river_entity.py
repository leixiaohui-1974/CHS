from .base_entity import BasePhysicalEntity
from chs_sdk.core.datastructures import Input

class RiverEntity(BasePhysicalEntity):
    """
    Represents a river segment which can be simulated using different
    dynamic models (e.g., for low flow vs. flood conditions).
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # A river entity expects an inflow
        self.input = Input(inflow=0)

    def step(self, dt: float, t: float):
        """
        The river entity's step method. It routes the entity's input to the
        currently active model before calling the main step logic.
        """
        active_model = self.dynamic_model_bank[self.active_dynamic_model_id]

        # --- Input Routing ---
        # This is where the entity directs its input to the active model.
        # This assumes both models have a compatible 'input.inflow' attribute.
        if hasattr(active_model, 'input') and hasattr(active_model.input, 'inflow'):
            active_model.input.inflow = self.input.inflow

        # Call the parent step method which executes the active model's step
        # and updates the entity's output from the model's output.
        super().step(dt, t)
