from typing import Optional
from water_system_simulator.modeling.base_model import BaseModel
from water_system_simulator.core.simulation_modes import SimulationMode

class BasePhysicalEntity(BaseModel):
    """
    A container for managing and switching between different fidelity models
    for a single physical object in the water system.
    """
    def __init__(self, name: str, steady_model: Optional[BaseModel] = None, dynamic_model: Optional[BaseModel] = None, precision_model: Optional[BaseModel] = None):
        super().__init__()
        self.name = name
        self.steady_model = steady_model
        self.dynamic_model = dynamic_model
        self.precision_model = precision_model
        self._active_model: Optional[BaseModel] = self.dynamic_model # Default to dynamic

    def step(self, simulation_mode: SimulationMode = SimulationMode.DYNAMIC, **kwargs):
        """
        Delegates the step call to the appropriate internal model based on the
        global simulation mode.

        Args:
            simulation_mode: The current simulation mode (STEADY, DYNAMIC, PRECISION).
            **kwargs: Additional arguments to pass to the model's step/solve method.
        """
        if simulation_mode == SimulationMode.STEADY:
            if not self.steady_model:
                raise NotImplementedError(f"Entity '{self.name}' does not have a steady-state model.")
            self._active_model = self.steady_model
            # Per instructions, steady model has a `solve` method
            if hasattr(self._active_model, 'solve'):
                self._active_model.solve(**kwargs)
            else:
                raise AttributeError(f"Steady model for '{self.name}' does not have a 'solve' method.")

        elif simulation_mode == SimulationMode.DYNAMIC:
            if not self.dynamic_model:
                raise NotImplementedError(f"Entity '{self.name}' does not have a dynamic model.")
            self._active_model = self.dynamic_model
            self._active_model.step(**kwargs)

        elif simulation_mode == SimulationMode.PRECISION:
            if not self.precision_model:
                raise NotImplementedError(f"Entity '{self.name}' does not have a precision model.")
            self._active_model = self.precision_model
            self._active_model.step(**kwargs)

        else:
            raise ValueError(f"Unknown simulation mode: {simulation_mode}")

        # The entity's output is the output of the active model
        if self._active_model:
            self.output = self._active_model.output

    def get_state(self):
        """
        Returns the state of the currently active model.
        """
        if self._active_model:
            return self._active_model.get_state()
        return {"status": "no_active_model"}
