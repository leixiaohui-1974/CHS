import numpy as np
from .base_controller import BaseController
from chs_sdk.core.datastructures import State, Input
from chs_sdk.modules.data_processing.pipeline import DataProcessingPipeline

class PIDController(BaseController):
    """
    A simple PID controller designed for the new simulation engine.
    It uses State and Input objects to manage its data.
    """
    def __init__(self, Kp, Ki, Kd, set_point, output_min=None, output_max=None, pipeline: DataProcessingPipeline = None, **kwargs):
        """
        Initializes the PID controller.

        Args:
            Kp (float): The proportional gain.
            Ki (float): The integral gain.
            Kd (float): The derivative gain.
            set_point (float): The desired setpoint.
            output_min (float, optional): The minimum limit for the output.
            output_max (float, optional): The maximum limit for the output.
            pipeline (DataProcessingPipeline, optional): A data processing pipeline
                                                         for smoothing the feedback signal.
        """
        super().__init__(**kwargs)
        # Parameters are stored directly
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.set_point = set_point
        self.output_min = output_min
        self.output_max = output_max
        self.data_pipeline = pipeline

        # State variables are grouped in the 'state' object
        self.state = State(integral=0.0, previous_error=0.0, output=0.0)

        # Input variables are grouped in the 'input' object
        # The simulation manager will write to these attributes.
        self.input = Input(error_source=0.0, current_value_offset=0.0)
        self.output = self.state.output # Expose a top-level output attribute

    def step(self, dt, error_source=None, **kwargs):
        """
        Calculates the control output based on values in self.input.
        Includes anti-windup logic (conditional integration).

        Args:
            dt (float): The time step.
            error_source (float, optional): The measured process variable. If provided,
                                           it updates `self.input.error_source`.
        """
        if dt <= 0:
            return

        # If error_source is passed as an argument, update the input state.
        # This makes the component compatible with the expressive execution_order.
        if error_source is not None:
            self.input.error_source = error_source

        # --- Optional: Process the feedback signal through a pipeline ---
        feedback_signal = self.input.error_source
        if self.data_pipeline:
            # The pipeline expects a dictionary.
            processed_data = self.data_pipeline.process({'feedback': feedback_signal})
            # The pipeline returns a dictionary. We expect a key that matches the input.
            feedback_signal = processed_data.get('feedback', feedback_signal)

        # The "error_source" is the measured process variable (e.g., water level)
        # An offset can be added to simulate sensor drift or other biases.
        measured_value = feedback_signal + self.input.current_value_offset
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
        self.output = self.state.output # Update top-level attribute
        return self.state.output

    def get_state(self):
        return self.state.__dict__
