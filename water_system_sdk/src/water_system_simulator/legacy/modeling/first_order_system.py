from .base_model import BaseModel

class FirstOrderSystem(BaseModel):
    """
    A simple discrete first-order linear system for testing estimators.
    Equation: y(k) = a1 * y(k-1) + b1 * u(k-1)
    """
    def __init__(self, a1: float, b1: float, initial_output: float = 0.0, **kwargs):
        super().__init__(**kwargs)
        self.a1 = a1
        self.b1 = b1
        self.prev_inflow = 0.0
        self.prev_outflow = initial_output
        self.output = initial_output

    def step(self, inflow: float):
        """
        Calculates the next output of the system.
        Args:
            inflow (float): The input to the system at time k, u(k).
        """
        current_outflow = self.a1 * self.prev_outflow + self.b1 * self.prev_inflow

        # Update state for next iteration
        self.prev_inflow = inflow
        self.prev_outflow = current_outflow
        self.output = current_outflow
        return self.output

    def get_state(self):
        return {"output": self.output}
