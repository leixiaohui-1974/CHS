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
        self.input = Input(error_source=0.0, current_value_offset=0.0)

    def step(self, dt, **kwargs):
        """
        Calculates the control output based on values in self.input.
        Includes anti-windup logic (conditional integration).

        Args:
            dt (float): The time step.
        """
        if dt <= 0:
            return

        # The "error_source" is the measured process variable (e.g., water level)
        # An offset can be added to simulate sensor drift or other biases.
        measured_value = self.input.error_source + self.input.current_value_offset
        error = self.set_point - measured_value

        # --- Calculate integral term with anti-windup ---
        # This is a simple and effective method.
        # We calculate the potential new integral first.
        new_integral = self.state.integral + error * dt

        # --- Calculate derivative term ---
        derivative = (error - self.state.previous_error) / dt

        # --- Calculate unbounded output ---
        # Note: We use the *potential* new integral term for this calculation.
        output = self.Kp * error + self.Ki * new_integral + self.Kd * derivative

        # --- Clamp output and apply anti-windup ---
        # If the output is saturated, we may need to prevent the integral from growing.
        clamped_output = output
        if self.output_max is not None and clamped_output > self.output_max:
            clamped_output = self.output_max
        if self.output_min is not None and clamped_output < self.output_min:
            clamped_output = self.output_min

        # If the output was NOT clamped, we can safely update the integral term.
        # This prevents "windup" when the controller hits its limits.
        if output == clamped_output:
             self.state.integral = new_integral

        # --- Update state for the next time step ---
        self.state.previous_error = error
        self.state.output = clamped_output

    def get_state(self):
        return self.state.__dict__
