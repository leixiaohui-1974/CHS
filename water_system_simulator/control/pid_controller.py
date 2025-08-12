import numpy as np

class PIDController:
    """
    A simple PID controller.
    """
    def __init__(self, kp, ki, kd, setpoint, output_min=None, output_max=None):
        """
        Initializes the PID controller.

        Args:
            kp (float): The proportional gain.
            ki (float): The integral gain.
            kd (float): The derivative gain.
            setpoint (float): The desired setpoint.
            output_min (float, optional): The minimum limit for the output. Defaults to None.
            output_max (float, optional): The maximum limit for the output. Defaults to None.
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_min = output_min
        self.output_max = output_max
        self.setpoint = setpoint
        self.integral = 0
        self.previous_error = 0
        self.output = 0.0

    def calculate(self, measured_value, dt):
        """
        Calculates the control output.

        Args:
            measured_value (float): The current measured value.
            dt (float): The time step.

        Returns:
            float: The control output.
        """
        error = self.setpoint - measured_value
        self.integral += error * dt
        derivative = (error - self.previous_error) / dt
        output = self.kp * error + self.ki * self.integral + self.kd * derivative

        # Clamp the output if limits are set
        if self.output_min is not None and self.output_max is not None:
            output = np.clip(output, self.output_min, self.output_max)
        elif self.output_min is not None:
            output = max(self.output_min, output)
        elif self.output_max is not None:
            output = min(self.output_max, output)

        self.output = output
        self.previous_error = error
        return self.output
