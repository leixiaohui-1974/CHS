import numpy as np
from dataclasses import dataclass, asdict
from .base_model import BaseModel
from chs_sdk.core.datastructures import State, Input

# --- ReservoirModel ---
@dataclass
class ReservoirState(State):
    level: float

@dataclass
class ReservoirInput(Input):
    inflow: float
    release_outflow: float
    demand_outflow: float

# --- MuskingumChannelModel ---
@dataclass
class MuskingumState(State):
    inflow_prev: float
    outflow_prev: float
    output: float

@dataclass
class MuskingumInput(Input):
    inflow: float

# --- FirstOrderInertiaModel ---
@dataclass
class FirstOrderInertiaState(State):
    storage: float
    output: float

@dataclass
class FirstOrderInertiaInput(Input):
    inflow: float


from typing import Union, Callable

class LinearTank(BaseModel):
    """
    A simple tank/reservoir model assuming a constant surface area (linear level-volume relationship).
    Renamed from ReservoirModel.
    """
    def __init__(self, area: float, initial_level: float, max_level: float = 999.0, min_level: float = 0.0, **kwargs):
        super().__init__(**kwargs)
        self.area = area
        self.max_level = max_level
        self.min_level = min_level
        self.level = initial_level
        self.output = self.level
        self.input: ReservoirInput = ReservoirInput(inflow=0.0, release_outflow=0.0, demand_outflow=0.0)

    def step(self, dt: float, **kwargs):
        """
        Updates the water level based on mass balance.
        """
        total_outflow = self.input.release_outflow + self.input.demand_outflow
        net_inflow = self.input.inflow - total_outflow
        dh = (net_inflow / self.area) * dt if self.area > 0 else 0

        self.level += dh
        self.level = np.clip(self.level, self.min_level, self.max_level)

        self.output = self.level
        return self.output

    def get_state(self):
        return {"level": self.level, "volume": self.level * self.area}


class NonlinearTank(BaseModel):
    """
    A nonlinear tank/reservoir model that uses a level-volume or level-area curve.
    """
    def __init__(self,
                 level_to_volume: Union[Callable[[float], float], np.ndarray],
                 initial_level: float,
                 max_level: float = 999.0,
                 min_level: float = 0.0,
                 **kwargs):
        super().__init__(**kwargs)
        self.max_level = max_level
        self.min_level = min_level
        self.input: ReservoirInput = ReservoirInput(inflow=0.0, release_outflow=0.0, demand_outflow=0.0)

        if isinstance(level_to_volume, np.ndarray) and level_to_volume.ndim == 2 and level_to_volume.shape[0] == 2:
            # Assumes a 2xN array: [[level1, level2...], [vol1, vol2...]]
            self._levels = level_to_volume[0]
            self._volumes = level_to_volume[1]
            self.get_volume = lambda level: np.interp(level, self._levels, self._volumes)
            self.get_level = lambda volume: np.interp(volume, self._volumes, self._levels)
        else:
            raise ValueError("level_to_volume must be a 2xN NumPy array where row 0 is levels and row 1 is volumes.")

        self.volume = self.get_volume(initial_level)
        self.level = initial_level
        self.output = self.level


    def step(self, dt: float, **kwargs):
        """
        Updates the volume and level based on mass balance.
        """
        total_outflow = self.input.release_outflow + self.input.demand_outflow
        net_inflow = self.input.inflow - total_outflow
        self.volume += net_inflow * dt

        # Clip volume based on min/max levels
        min_volume = self.get_volume(self.min_level)
        max_volume = self.get_volume(self.max_level)
        self.volume = np.clip(self.volume, min_volume, max_volume)

        # Update level from the new volume
        self.level = self.get_level(self.volume)
        self.output = self.level
        return self.output

    def get_state(self):
        return {"level": self.level, "volume": self.volume}

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
        self.state: MuskingumState = MuskingumState(inflow_prev=initial_inflow, outflow_prev=initial_outflow, output=initial_outflow)
        self.input: MuskingumInput = MuskingumInput(inflow=initial_inflow)
        self.output = self.state.output # Set initial output

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
                           self.C2 * self.state.inflow_prev +
                           self.C3 * self.state.outflow_prev)

        self.state.inflow_prev = self.input.inflow
        self.state.outflow_prev = outflow_current
        self.state.output = outflow_current
        self.output = outflow_current
        return self.output

    def get_state(self):
        return asdict(self.state)

class FirstOrderInertiaModel(BaseModel):
    """
    Represents a storage object with first-order inertia characteristics.
    Refactored to use State and Input objects.
    """
    def __init__(self, initial_storage, time_constant, solver_class, dt, **kwargs):
        super().__init__(**kwargs)
        self.time_constant = time_constant
        self.state: FirstOrderInertiaState = FirstOrderInertiaState(storage=initial_storage, output=0.0)
        self.input: FirstOrderInertiaInput = FirstOrderInertiaInput(inflow=0.0)

        def ode_func(t, y):
            outflow = y / self.time_constant if self.time_constant > 0 else 0
            return self.input.inflow - outflow

        self.solver = solver_class(f=ode_func, dt=dt)
        self.state.output = initial_storage / time_constant if time_constant > 0 else 0
        self.output = self.state.output # Set initial output

    def step(self, t, **kwargs):
        """
        Performs a single simulation step using the selected solver.
        """
        self.state.storage = self.solver.step(t, self.state.storage)
        outflow = self.state.storage / self.time_constant if self.time_constant > 0 else 0
        self.state.output = outflow
        self.output = outflow
        return self.output

    def get_state(self):
        return asdict(self.state)
