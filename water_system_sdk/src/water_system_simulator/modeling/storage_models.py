import numpy as np
from .base_model import BaseModel
from ..core.datastructures import State, Input

class ReservoirModel(BaseModel):
    """
    A simple reservoir model based on mass balance.
    """
    def __init__(self, area, initial_level, max_level=20.0, **kwargs):
        super().__init__(**kwargs)
        self.area = area
        self.max_level = max_level
        self._state = State(level=initial_level)
        self.input = Input(inflow=0.0, release_outflow=0.0, demand_outflow=0.0)
        self.output = self._state.level # Set initial output

    def step(self, dt, **kwargs):
        """
        Updates the water level in the reservoir.
        """
        total_outflow = self.input.release_outflow + self.input.demand_outflow
        dh = (self.input.inflow - total_outflow) / self.area * dt
        level = self._state.level + dh

        if level > self.max_level:
            level = self.max_level
        elif level < 0:
            level = 0

        self._state.level = level
        self.output = level

    def get_state(self):
        return self._state.__dict__

class MuskingumChannelModel(BaseModel):
    """
    Represents a channel reach using the Muskingum routing model.
    Refactored to use State and Input objects.
    """
    def __init__(self, K: float, x: float, dt: float, initial_inflow: float, initial_outflow: float, **kwargs):
        super().__init__(**kwargs)
        self.K = K
        self.x = x
        self.dt = dt
        self._state = State(inflow_prev=initial_inflow, outflow_prev=initial_outflow, output=initial_outflow)
        self.input = Input(inflow=initial_inflow)
        self.output = self._state.output # Set initial output

        denominator = self.K - self.K * self.x + 0.5 * self.dt
        if denominator == 0:
            raise ValueError("Muskingum parameters and dt result in a zero denominator.")

        self.C1 = (0.5 * self.dt - self.K * self.x) / denominator
        self.C2 = (0.5 * self.dt + self.K * self.x) / denominator
        self.C3 = (self.K - self.K * self.x - 0.5 * self.dt) / denominator

    def step(self, **kwargs):
        """
        Performs a single routing step using data from self.input.
        """
        outflow_current = (self.C1 * self.input.inflow +
                           self.C2 * self._state.inflow_prev +
                           self.C3 * self._state.outflow_prev)

        self._state.inflow_prev = self.input.inflow
        self._state.outflow_prev = outflow_current
        self._state.output = outflow_current
        self.output = outflow_current
        return self.output

    def get_state(self):
        return self._state.__dict__

class FirstOrderInertiaModel(BaseModel):
    """
    Represents a storage object with first-order inertia characteristics.
    Refactored to use State and Input objects.
    """
    def __init__(self, initial_storage, time_constant, solver_class, dt, **kwargs):
        super().__init__(**kwargs)
        self.time_constant = time_constant
        self._state = State(storage=initial_storage, output=0.0)
        self.input = Input(inflow=0.0)

        def ode_func(t, y):
            outflow = y / self.time_constant if self.time_constant > 0 else 0
            return self.input.inflow - outflow

        self.solver = solver_class(f=ode_func, dt=dt)
        self._state.output = initial_storage / time_constant if time_constant > 0 else 0
        self.output = self._state.output # Set initial output

    def step(self, t, **kwargs):
        """
        Performs a single simulation step using the selected solver.
        """
        self._state.storage = self.solver.step(t, self._state.storage)
        outflow = self._state.storage / self.time_constant if self.time_constant > 0 else 0
        self._state.output = outflow
        self.output = outflow
        return self.output

    def get_state(self):
        return self._state.__dict__
