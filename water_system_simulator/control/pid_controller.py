class PIDController:
    """
    A simple PID controller.
    """
    def __init__(self, kp, ki, kd, setpoint):
        """
        Initializes the PID controller.

        Args:
            kp (float): The proportional gain.
            ki (float): The integral gain.
            kd (float): The derivative gain.
            setpoint (float): The desired setpoint.
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
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
        self.output = self.kp * error + self.ki * self.integral + self.kd * derivative
        self.previous_error = error
        return self.output
