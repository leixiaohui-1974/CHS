import numpy as np
from ..base_model import BaseModel

class MuskingumModel(BaseModel):
    """
    Implements the Muskingum method for hydrologic channel routing.
    """
    def __init__(self, K: float, x: float, dt: float, initial_outflow: float = 0.0, **kwargs):
        """
        Initializes the Muskingum routing model.

        Args:
            K (float): The storage time constant for the reach (in seconds).
            x (float): A dimensionless weighting factor (usually between 0 and 0.5).
            dt (float): The simulation time step (in seconds).
            initial_outflow (float, optional): The initial outflow from the reach (m^3/s).
        """
        super().__init__(**kwargs)
        self.K = K
        self.x = x
        self.dt = dt

        # Denominator for coefficients
        denominator = 2 * self.K * (1 - self.x) + self.dt
        if denominator == 0:
            raise ValueError("Model denominator is zero. Check K, x, and dt values.")

        # Calculate Muskingum coefficients
        self.C1 = (self.dt - 2 * self.K * self.x) / denominator
        self.C2 = (self.dt + 2 * self.K * self.x) / denominator
        self.C3 = (2 * self.K * (1 - self.x) - self.dt) / denominator

        # Check for stability
        if not (0 <= 2 * self.K * self.x <= self.dt):
            print("Warning: Muskingum model may be unstable. Condition (0 <= 2*K*x <= dt) is not met.")

        # State variables
        self.inflow_prev = initial_outflow  # Assume initial steady state
        self.outflow_prev = initial_outflow
        self.outflow = initial_outflow
        self.output = self.outflow

    def step(self, inflow: float, **kwargs):
        """
        Performs one step of the Muskingum routing calculation.

        Args:
            inflow (float): The inflow to the reach at the current time step (m^3/s).
        """
        # Muskingum equation: O_t = C1*I_t + C2*I_{t-1} + C3*O_{t-1}
        self.outflow = (self.C1 * inflow +
                        self.C2 * self.inflow_prev +
                        self.C3 * self.outflow_prev)

        # Ensure outflow is non-negative
        self.outflow = max(0, self.outflow)
        self.output = self.outflow

        # Update state for the next time step
        self.inflow_prev = inflow
        self.outflow_prev = self.outflow

        return self.output

    def get_state(self):
        """
        Returns the current state of the model.
        """
        return {"outflow": self.outflow, "output": self.output}
