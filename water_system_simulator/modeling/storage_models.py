import numpy as np
from .base_model import BaseModel

class MuskingumChannelModel(BaseModel):
    """
    Represents a channel reach using the Muskingum routing model.
    """
    def __init__(self, K: float, x: float, dt: float, initial_inflow: float, initial_outflow: float):
        """
        Initializes the Muskingum channel model.

        Args:
            K (float): The storage time constant for the reach.
            x (float): A dimensionless weighting factor (0 <= x <= 0.5).
            dt (float): The simulation time step.
            initial_inflow (float): The initial inflow to the reach.
            initial_outflow (float): The initial outflow from the reach.
        """
        self.K = K
        self.x = x
        self.dt = dt

        # Initial states
        self.inflow_prev = initial_inflow
        self.outflow_prev = initial_outflow
        self.output = initial_outflow

        # Calculate Muskingum coefficients
        denominator = self.K - self.K * self.x + 0.5 * self.dt
        if denominator == 0:
            raise ValueError("Muskingum parameters and dt result in a zero denominator.")

        self.C1 = (0.5 * self.dt - self.K * self.x) / denominator
        self.C2 = (0.5 * self.dt + self.K * self.x) / denominator
        self.C3 = (self.K - self.K * self.x - 0.5 * self.dt) / denominator

        # Stability check
        if not (0 <= 2 * self.K * self.x <= self.dt):
             print(f"Warning: Muskingum parameters may lead to instability. "
                   f"Ensure 2*K*x ({2*self.K*self.x:.2f}) <= dt ({self.dt:.2f}).")

    def step(self, inflow: float):
        """
        Performs a single routing step.
        O_t+1 = C1*I_t+1 + C2*I_t + C3*O_t

        Args:
            inflow (float): The inflow to the reach at the current time step (I_t+1).

        Returns:
            float: The outflow from the reach at the current time step (O_t+1).
        """
        outflow_current = (self.C1 * inflow +
                           self.C2 * self.inflow_prev +
                           self.C3 * self.outflow_prev)

        # Update states for the next time step
        self.inflow_prev = inflow
        self.outflow_prev = outflow_current
        self.output = outflow_current

        return self.output

class FirstOrderInertiaModel(BaseModel):
    """
    Represents a storage object with first-order inertia characteristics.
    This model can represent a reservoir or a lake.
    """
    def __init__(self, initial_storage, time_constant):
        """
        Initializes the first-order inertia model.

        Args:
            initial_storage (float): The initial storage of the object.
            time_constant (float): The time constant of the model (T).
        """
        self.storage = initial_storage
        self.time_constant = time_constant
        self.output = initial_storage / time_constant if time_constant else 0.0

    def step(self, inflow):
        """
        Performs a single simulation step.

        Args:
            inflow (float): The inflow to the object at the current time step.

        Returns:
            float: The outflow from the object at the current time step.
        """
        # The outflow is proportional to the storage.
        outflow = self.storage / self.time_constant

        # Update storage based on inflow and outflow.
        d_storage_dt = inflow - outflow
        self.storage += d_storage_dt

        self.output = outflow
        return self.output
