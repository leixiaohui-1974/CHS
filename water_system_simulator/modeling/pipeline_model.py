import numpy as np
from .base_model import BaseModel

class PipelineModel(BaseModel):
    """
    Represents a simple pressurized pipeline, considering friction and inertia.
    Uses the Darcy-Weisbach equation for friction loss.
    """
    def __init__(self, length: float, diameter: float, friction_factor: float, initial_flow: float = 0.0):
        """
        Initializes the Pipeline model.

        Args:
            length (float): Length of the pipeline (m).
            diameter (float): Diameter of the pipeline (m).
            friction_factor (float): Darcy-Weisbach friction factor (dimensionless).
            initial_flow (float, optional): Initial flow rate (m^3/s). Defaults to 0.0.
        """
        super().__init__()
        self.length = length
        self.diameter = diameter
        self.friction_factor = friction_factor

        self.area = np.pi * (self.diameter ** 2) / 4
        self.flow = initial_flow
        self.output = initial_flow  # Primary output is flow rate
        self.g = 9.81

    def step(self, inlet_pressure: float, outlet_pressure: float, dt: float):
        """
        Calculates the flow for the next time step by updating internal state.

        Args:
            inlet_pressure (float): Pressure at the inlet (in meters of head).
            outlet_pressure (float): Pressure at the outlet (in meters of head).
            dt (float): Simulation time step (s).
        """
        # 1. Calculate current velocity
        velocity = self.flow / self.area if self.area > 0 else 0

        # 2. Calculate head loss due to friction (Darcy-Weisbach equation)
        # h_f = f * (L/D) * (v^2 / 2g)
        head_loss_friction = (self.friction_factor * (self.length / self.diameter) *
                              (velocity**2 / (2 * self.g))) if velocity != 0 else 0

        # Make sure head loss acts against the direction of flow
        head_loss_friction *= np.sign(velocity)

        # 3. Calculate net head driving the acceleration
        delta_h_pressure = inlet_pressure - outlet_pressure
        net_head = delta_h_pressure - head_loss_friction

        # 4. Calculate acceleration of the water column (from F=ma -> a = g*h/L)
        acceleration = (self.g * net_head) / self.length

        # 5. Update velocity and flow using Euler's method
        new_velocity = velocity + acceleration * dt
        self.flow = new_velocity * self.area
        self.output = self.flow

    def get_state(self):
        """
        Returns a dictionary of the model's current state.
        """
        return {
            "flow": self.flow,
            "output": self.output
        }
