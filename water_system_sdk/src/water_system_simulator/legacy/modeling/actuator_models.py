from .base_model import BaseModel
from dataclasses import dataclass, field
import numpy as np
import time

@dataclass
class ActuatorState:
    """Represents the state of an actuator."""
    current_setpoint: float = 0.0
    actual_position: float = 0.0
    last_update_time: float = field(default_factory=time.time)

class ActuatorBase(BaseModel):
    """
    Base class for all actuators, modeling dynamic behaviors.

    This class simulates real-world actuator limitations such as response time (slew rate),
    deadband, and hysteresis.
    """
    def __init__(self,
                 initial_position: float = 0.0,
                 slew_rate: float = float('inf'),  # units/sec. Inf means instantaneous.
                 deadband: float = 0.0,            # The range around a setpoint where no action is taken.
                 hysteresis: float = 0.0,          # The difference in response based on direction of travel.
                 **kwargs):
        super().__init__(**kwargs)
        if slew_rate <= 0:
            raise ValueError("Slew rate must be positive.")
        if deadband < 0:
            raise ValueError("Deadband cannot be negative.")
        if hysteresis < 0:
            raise ValueError("Hysteresis cannot be negative.")

        self.slew_rate = slew_rate
        self.deadband = deadband
        self.hysteresis = hysteresis

        self.state = ActuatorState(
            current_setpoint=initial_position,
            actual_position=initial_position,
            last_update_time=time.time() # or a simulation time from context
        )
        self.target_setpoint = initial_position

    def set_target(self, setpoint: float):
        """
        Set the desired target position for the actuator.
        The actuator will start moving towards this target in subsequent update steps.
        """
        self.target_setpoint = setpoint

    def update(self, dt: float):
        """
        Update the actuator's actual position based on its dynamics.
        This method should be called at each simulation step.

        Args:
            dt (float): The time elapsed since the last update (simulation time step).
        """
        # 1. Apply Deadband: Only update the internal setpoint if the new target is outside the deadband.
        if abs(self.target_setpoint - self.state.current_setpoint) > self.deadband:
            self.state.current_setpoint = self.target_setpoint

        # 2. Determine target position considering hysteresis
        effective_target = self.state.current_setpoint
        direction_of_travel = np.sign(effective_target - self.state.actual_position)

        if direction_of_travel > 0: # Moving "up"
            effective_target -= self.hysteresis / 2.0
        elif direction_of_travel < 0: # Moving "down"
            effective_target += self.hysteresis / 2.0

        # 3. Apply Slew Rate: Calculate the maximum possible change in position
        max_change = self.slew_rate * dt
        current_pos = self.state.actual_position
        desired_change = effective_target - current_pos

        # 4. Update actual position
        if abs(desired_change) <= max_change:
            self.state.actual_position = effective_target
        else:
            self.state.actual_position += direction_of_travel * max_change

    def get_current_position(self) -> float:
        """Returns the current, actual position of the actuator."""
        return self.state.actual_position

    def get_state(self):
        """Returns the state of the actuator."""
        return {
            "target_setpoint": self.target_setpoint,
            "current_setpoint": self.state.current_setpoint,
            "actual_position": self.state.actual_position,
        }
