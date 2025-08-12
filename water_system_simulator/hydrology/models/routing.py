from .base import RoutingModel

class MuskingumModel(RoutingModel):
    """
    Implements the Muskingum method for river routing.
    """
    def __init__(self, parameters):
        super().__init__(parameters)
        # Model parameters
        self.K = self.params.get("K", 24)  # Storage time constant (hours)
        self.x = self.params.get("x", 0.2)  # Weighting factor
        self.dt = self.params.get("dt", 1) # Time step (hours), should be passed from simulation

        # Check for stability criteria
        if not (0 <= self.x <= 0.5):
            raise ValueError("Muskingum parameter x must be between 0 and 0.5.")
        if not (2 * self.K * self.x <= self.dt <= self.K):
             # This is a common rule of thumb, but we will allow it to be flexible
             # For a robust model, we might want to enforce this or warn the user
             pass

        # Calculate coefficients
        denominator = 2 * self.K * (1 - self.x) + self.dt
        self.C1 = (self.dt - 2 * self.K * self.x) / denominator
        self.C2 = (self.dt + 2 * self.K * self.x) / denominator
        self.C3 = (2 * self.K * (1 - self.x) - self.dt) / denominator

        # Model states
        self.I_prev = self.states.get("initial_inflow", 0.0)
        self.O_prev = self.states.get("initial_outflow", 0.0)

    def route(self, inflow):
        """
        Routes the inflow for one time step.

        Args:
            inflow (float): The inflow to the reach at the current time step (I_t).

        Returns:
            float: The outflow from the reach at the current time step (O_t).
        """
        I_t = inflow

        # Muskingum equation: O_t = C1*I_t + C2*I_{t-1} + C3*O_{t-1}
        O_t = self.C1 * I_t + self.C2 * self.I_prev + self.C3 * self.O_prev

        # Update states for the next time step
        self.I_prev = I_t
        self.O_prev = O_t

        return max(0, O_t)
