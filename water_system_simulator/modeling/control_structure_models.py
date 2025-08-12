import numpy as np

class GateModel:
    """
    Represents a gate using the orifice flow equation.
    """
    def __init__(self, discharge_coefficient, area):
        """
        Initializes the gate model.

        Args:
            discharge_coefficient (float): The discharge coefficient of the gate.
            area (float): The area of the gate opening.
        """
        self.discharge_coefficient = discharge_coefficient
        self.area = area
        self.g = 9.81  # acceleration due to gravity
        self.flow = 0.0 # Initial flow

    def step(self, upstream_level, downstream_level, area):
        """
        Calculates the flow through the gate for the current time step.

        Args:
            upstream_level (float): The water level upstream of the gate.
            downstream_level (float): The water level downstream of the gate.
            area (float): The area of the gate opening.

        Returns:
            float: The flow rate through the gate.
        """
        self.area = area # Update area state
        head_diff = upstream_level - downstream_level
        if head_diff <= 0 or self.area <=0:
            self.flow = 0.0
            return 0.0

        self.flow = self.discharge_coefficient * self.area * np.sqrt(2 * self.g * head_diff)
        return self.flow

class PumpModel:
    """
    Represents a pump with a simple characteristic curve.
    """
    def __init__(self, max_flow, max_head):
        """
        Initializes the pump model.

        Args:
            max_flow (float): The maximum flow rate of the pump.
            max_head (float): The maximum head the pump can overcome.
        """
        self.max_flow = max_flow
        self.max_head = max_head

    def calculate_flow(self, head_diff, speed):
        """
        Calculates the flow rate of the pump.

        Args:
            head_diff (float): The head difference the pump is working against.
            speed (float): The speed of the pump (0 to 1).

        Returns:
            float: The flow rate of the pump.
        """
        if speed <= 0:
            return 0.0

        # Simple linear pump curve
        flow = self.max_flow * (1 - head_diff / self.max_head) * speed

        return max(0.0, flow)
