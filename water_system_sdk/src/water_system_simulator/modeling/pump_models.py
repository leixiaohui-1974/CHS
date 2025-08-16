import numpy as np
from .actuator_models import ActuatorBase
from typing import Callable

class PumpBase(ActuatorBase):
    """
    Base class for pump models.
    """
    def __init__(self, initial_speed: float = 1.0, **kwargs):
        # Pump speed (0-1) is the actuator position
        super().__init__(initial_position=initial_speed, **kwargs)
        self.flow = 0.0
        self.head = 0.0
        self.power = 0.0
        self.efficiency = 0.0
        self.output = self.flow

    def set_speed(self, speed: float):
        """
        Set the target speed of the pump.

        Args:
            speed (float): The desired speed as a fraction of max speed (0.0 to 1.0).
        """
        self.set_target(np.clip(speed, 0, 1))

    def get_current_speed(self) -> float:
        """Returns the current operating speed as a fraction (0-1)."""
        return np.clip(self.get_current_position(), 0, 1)

    def step(self, system_head: float, dt: float, **kwargs):
        """
        Updates the pump's state and calculates flow, head, etc.
        Must be implemented by subclasses.
        """
        raise NotImplementedError

class CentrifugalPump(PumpBase):
    """
    A centrifugal pump model based on H-Q and Eff-Q curves.
    Supports Variable Frequency Drives (VFD) through affinity laws.
    """
    def __init__(self,
                 hq_curve: Callable[[float], float], # Head (H) as a function of flow (Q)
                 eff_q_curve: Callable[[float], float], # Efficiency (Eff) as a function of flow (Q)
                 **kwargs):
        super().__init__(**kwargs)
        self.hq_curve = hq_curve
        self.eff_q_curve = eff_q_curve

    def step(self, system_head: float, dt: float, **kwargs):
        # Update actuator position (speed)
        self.update(dt)
        speed_ratio = self.get_current_speed()

        if speed_ratio <= 0:
            self.flow = self.head = self.efficiency = self.power = 0.0
            self.output = self.flow
            return self.output

        # We need to find the operating point where pump head equals system head.
        # Pump Head Curve at new speed: H_p(Q) = H_rated(Q/alpha) * alpha^2
        # We need to solve H_p(Q) = system_head for Q.
        # A robust way is to find the intersection of the pump curve and system curve.
        # H_pump(Q, alpha) = system_head(Q)
        # For now, we assume system_head is a single value, not a curve.

        try:
            # Simplified approach: Use affinity laws to find the equivalent head at rated speed
            equivalent_head = system_head / (speed_ratio**2) if speed_ratio > 0 else float('inf')

            # Find the flow at rated speed for this equivalent head.
            # This requires an inverse of the HQ curve or a root-finding solver.
            # We'll use a simple search for this example.
            q_rated = 0
            # A simple search to find the flow (q_rated) at which the pump provides the equivalent_head
            # This is a placeholder for a more robust root-finding algorithm (e.g., Newton's method)
            for q_test in np.linspace(0, 50, 500): # Scan a reasonable flow range, increased from 10 to 50
                if self.hq_curve(q_test) < equivalent_head:
                    q_rated = q_test
                    # This simple break finds the *first* time the pump head drops below
                    # the system head, which is a rough approximation of the operating point.
                    break

            if q_rated > 0:
                # Apply affinity law for flow
                self.flow = q_rated * speed_ratio
                self.head = self.hq_curve(q_rated) * (speed_ratio**2)

                # Get efficiency and power
                self.efficiency = self.eff_q_curve(q_rated) # Efficiency curve is ~constant with speed
                if self.flow > 0 and self.head > 0 and self.efficiency > 0:
                    g = 9.81
                    rho = 1000
                    # Power in Watts
                    self.power = (rho * g * self.flow * self.head) / self.efficiency
                else:
                    self.power = 0
            else:
                self.flow = self.head = self.efficiency = self.power = 0.0

        except Exception:
            self.flow = self.head = self.efficiency = self.power = 0.0

        self.output = self.flow
        return self.output

class PositiveDisplacementPump(PumpBase):
    """
    A positive displacement pump model with nearly constant flow regardless of head.
    """
    def __init__(self, rated_flow: float, **kwargs):
        super().__init__(**kwargs)
        self.rated_flow = rated_flow

    def step(self, system_head: float, dt: float, **kwargs):
        self.update(dt)
        speed_ratio = self.get_current_speed()

        # Flow is directly proportional to speed
        self.flow = self.rated_flow * speed_ratio
        self.head = system_head # Pump provides whatever head is needed
        self.output = self.flow
        # Power/efficiency would need to be calculated based on a curve
        self.power = 0 # Placeholder
        self.efficiency = 0 # Placeholder
        return self.output

class AxialFlowPump(CentrifugalPump):
    """
    An axial flow pump, characterized by a steep H-Q curve and high flow, low head.
    Inherits from CentrifugalPump, just uses a different curve shape typically.
    The implementation is identical, the difference is in the user-provided curves.
    """
    pass
