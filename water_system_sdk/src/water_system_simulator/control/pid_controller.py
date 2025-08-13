import numpy as np
from .base_controller import BaseController
from ..core.datastructures import State, Input

class PIDController(BaseController):
    """
    A simple PID controller designed for the new simulation engine.
    It uses State and Input objects to manage its data.
    """
    def __init__(self, Kp, Ki, Kd, set_point, output_min=None, output_max=None, **kwargs):
        """
        Initializes the PID controller.

        Args:
            Kp (float): The proportional gain.
            Ki (float): The integral gain.
            Kd (float): The derivative gain.
            set_point (float): The desired setpoint.
            output_min (float, optional): The minimum limit for the output.
            output_max (float, optional): The maximum limit for the output.
        """
        super().__init__(**kwargs)
        # Parameters are stored directly
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.set_point = set_point
        self.output_min = output_min
        self.output_max = output_max

        # State variables are grouped in the 'state' object
        self.state = State(integral=0.0, previous_error=0.0, output=0.0)

        # Input variables are grouped in the 'input' object
        # The simulation manager will write to these attributes.
        self.input = Input(error_source=0.0)

    def step(self, dt, **kwargs):
        """
        Calculates the control output based on values in self.input.

        Args:
            dt (float): The time step.
        """
        # The "error_source" is the measured process variable (e.g., water level)
        error = self.set_point - self.input.error_source

        integral = self.state.integral + error * dt
        derivative = (error - self.state.previous_error) / dt if dt > 0 else 0.0

        output = self.Kp * error + self.Ki * integral + self.Kd * derivative

        # Clamp the output if limits are set
        if self.output_min is not None:
            output = max(self.output_min, output)
        if self.output_max is not None:
            output = min(self.output_max, output)

        # Update state for the next time step
        self.state.integral = integral
        self.state.previous_error = error
        self.state.output = output

    def get_state(self):
        return self.state.__dict__
