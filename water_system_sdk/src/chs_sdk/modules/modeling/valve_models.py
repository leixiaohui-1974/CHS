import numpy as np
from .actuator_models import ActuatorBase
from typing import Callable, Union

class ValveBase(ActuatorBase):
    """
    Base class for valve models.
    Calculates flow based on opening percentage, pressure difference, and flow coefficient (Cv).
    """
    def __init__(self,
                 cv_curve: Union[Callable[[float], float], list], # Curve mapping opening % (0-1) to Cv
                 initial_opening: float = 0.0, # as a fraction (0 to 1)
                 **kwargs):
        # Pass actuator-related kwargs to ActuatorBase
        super().__init__(initial_position=initial_opening, **kwargs)
        self.cv_curve = cv_curve
        self.flow = 0.0

        # Ensure initial position is within 0-1 range
        self.state.actual_position = np.clip(initial_opening, 0, 1)
        self.target_setpoint = np.clip(initial_opening, 0, 1)


    def set_opening(self, percentage: float):
        """
        Set the target opening of the valve.

        Args:
            percentage (float): The desired opening as a fraction (0.0 to 1.0).
        """
        self.set_target(np.clip(percentage, 0, 1))

    def get_cv(self, opening: float) -> float:
        """
        Calculates the flow coefficient (Cv) for a given opening percentage.
        """
        opening = np.clip(opening, 0, 1)
        if isinstance(self.cv_curve, list):
            # Assumes list is a lookup table for 0, 10, 20... 100% opening
            # Linear interpolation between points
            num_points = len(self.cv_curve)
            if num_points < 2: return self.cv_curve[0] if num_points == 1 else 0

            pos = opening * (num_points - 1)
            idx = int(pos)
            frac = pos - idx

            if idx >= num_points - 1:
                return self.cv_curve[-1]

            val1 = self.cv_curve[idx]
            val2 = self.cv_curve[idx+1]
            return val1 + (val2 - val1) * frac

        else:
            # Assumes it's a callable function
            return self.cv_curve(opening)

    def step(self, upstream_pressure: float, downstream_pressure: float, dt: float, command: float = None):
        """
        Updates the valve's state and calculates flow.

        Args:
            upstream_pressure (float): Pressure upstream of the valve (e.g., in meters of head).
            downstream_pressure (float): Pressure downstream of the valve.
            dt (float): Simulation time step.
        """
        if command is not None:
            self.set_opening(command)

        # First, update the actuator's physical position
        self.update(dt)
        current_opening = self.get_current_position()
        current_opening = np.clip(current_opening, 0, 1) # ensure physical limits

        # Calculate flow based on the current physical opening
        cv = self.get_cv(current_opening)
        delta_p = upstream_pressure - downstream_pressure

        if delta_p > 0 and cv > 0:
            # Using the standard Cv formula for liquids: Q = Cv * sqrt(dP/SG)
            # Assuming water (SG=1) and pressure in meters of head.
            # A more rigorous implementation would require fluid density/SG and proper unit conversion.
            # For now, we assume Cv is given in units compatible with m^3/s and meters of head.
            self.flow = cv * np.sqrt(delta_p)
        else:
            self.flow = 0.0

        self.output = self.flow
        return self.output

    def get_current_opening(self) -> float:
        """Returns the current opening as a fraction (0-1)."""
        return np.clip(self.get_current_position(), 0, 1)

class GenericValve(ValveBase):
    """
    A generic valve where the user provides the Cv curve directly.
    """
    def __init__(self, cv_curve: Union[Callable[[float], float], list], **kwargs):
        super().__init__(cv_curve=cv_curve, **kwargs)

class BallValve(ValveBase):
    """
    A ball valve model with a typical equal-percentage characteristic curve.
    """
    def __init__(self, cv_max: float, **kwargs):
        # Equal percentage curve: Cv = Cv_max * R^(x-1)
        # A common turn-down ratio (R) is 50.
        R = 50
        def cv_curve(opening): # opening is 0-1
            if opening <= 0: return 0
            return cv_max * (R ** (opening - 1))
        super().__init__(cv_curve=cv_curve, **kwargs)

class ButterflyValve(ValveBase):
    """
    A butterfly valve model with a typical linear-to-equal-percentage curve.
    This is a simplified polynomial approximation.
    """
    def __init__(self, cv_max: float, **kwargs):
        def cv_curve(opening): # opening is 0-1
            # A simple cubic approximation for a characteristic butterfly curve
            return cv_max * (-2 * opening**3 + 3 * opening**2)
        super().__init__(cv_curve=cv_curve, **kwargs)
