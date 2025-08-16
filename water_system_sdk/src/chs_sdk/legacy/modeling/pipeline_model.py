import numpy as np
from .base_model import BaseModel
from collections import deque

class PipelineModel(BaseModel):
    """
    Represents a pressurized pipeline, calculating flow based on friction loss
    and simulating basic water quality (advection).
    """
    def __init__(self,
                 length: float,
                 diameter: float,
                 method: str = 'darcy_weisbach',
                 friction_factor: float = 0.02, # For Darcy-Weisbach
                 hazen_williams_c: float = 100, # For Hazen-Williams
                 initial_flow: float = 0.0,
                 initial_concentration: float = 0.0,
                 quality_steps: int = 10, # Number of cells for quality routing
                 **kwargs):
        super().__init__(**kwargs)
        self.length = length
        self.diameter = diameter
        self.method = method.lower()
        self.friction_factor = friction_factor
        self.hazen_williams_c = hazen_williams_c

        self.area = np.pi * (self.diameter ** 2) / 4
        self.flow = initial_flow
        self.output = initial_flow
        self.g = 9.81

        # Water quality attributes
        self.quality_steps = max(1, quality_steps)
        self.cell_length = self.length / self.quality_steps
        self.cell_volume = self.area * self.cell_length
        # Use a deque for efficient advection simulation
        self.concentrations = deque([initial_concentration] * self.quality_steps, maxlen=self.quality_steps)
        self._flow_volume_accumulator = 0.0

    def _calculate_head_loss(self, velocity):
        """Calculates friction head loss based on the selected method."""
        if abs(velocity) < 1e-6:
            return 0.0

        if self.method == 'darcy_weisbach':
            # h_f = f * (L/D) * (v^2 / 2g)
            return (self.friction_factor * (self.length / self.diameter) *
                    (velocity**2 / (2 * self.g)))
        elif self.method == 'hazen_williams':
            # h_f = 10.67 * L * (Q/C)^1.852 / D^4.87
            # This formula is for SI units (Q in m3/s, D,L in m)
            q = velocity * self.area
            head_loss = (10.67 * self.length / (self.hazen_williams_c**1.852 * self.diameter**4.87)) * abs(q)**1.852
            return head_loss
        else:
            raise ValueError(f"Unknown friction loss method: {self.method}")

    def step(self, inlet_pressure: float, outlet_pressure: float, dt: float, **kwargs):
        """
        Calculates the flow for the next time step (hydraulic step).
        """
        velocity = self.flow / self.area if self.area > 0 else 0

        head_loss_friction = self._calculate_head_loss(velocity)
        head_loss_friction *= np.sign(velocity)

        delta_h_pressure = inlet_pressure - outlet_pressure
        net_head = delta_h_pressure - head_loss_friction

        acceleration = (self.g * net_head) / self.length if self.length > 0 else 0
        new_velocity = velocity + acceleration * dt
        self.flow = new_velocity * self.area
        self.output = self.flow

        # Also update quality in the same step for convenience
        # In a real co-simulation, this might be separate
        if 'upstream_concentration' in kwargs:
            self.update_quality(kwargs['upstream_concentration'], dt)

    def update_quality(self, upstream_concentration: float, dt: float):
        """
        Updates the water quality in the pipeline (quality step).
        Simulates 1D advection by shifting concentrations between cells.
        """
        if self.cell_volume < 1e-6: return

        # Accumulate flowed volume
        self._flow_volume_accumulator += abs(self.flow) * dt

        # Number of cells to shift
        num_shifts = int(self._flow_volume_accumulator / self.cell_volume)

        if num_shifts > 0:
            for _ in range(num_shifts):
                self.concentrations.appendleft(upstream_concentration)
            # Reset accumulator, keeping the remainder
            self._flow_volume_accumulator %= self.cell_volume

    def get_outlet_concentration(self) -> float:
        """Returns the concentration at the pipe outlet."""
        return self.concentrations[-1] # Outlet is the end of the deque

    def get_state(self):
        return {
            "flow": self.flow,
            "velocity": self.flow / self.area if self.area > 0 else 0,
            "outlet_concentration": self.get_outlet_concentration(),
            "concentration_profile": list(self.concentrations)
        }
