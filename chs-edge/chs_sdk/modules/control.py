class PIDController:
    """
    A mock implementation of the PIDController for the MVP.
    """
    def __init__(self, setpoint: float, kp: float, ki: float, kd: float):
        self.setpoint = setpoint
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self._prev_error = 0
        self._integral = 0
        print(f"[MOCK SDK] PIDController initialized with setpoint={setpoint}, Kp={kp}, Ki={ki}, Kd={kd}")

    def calculate(self, measured_value: float, dt: float) -> float:
        """
        Calculates the control variable.
        """
        error = self.setpoint - measured_value
        self._integral += error * dt
        derivative = (error - self._prev_error) / dt
        output = self.kp * error + self.ki * self._integral + self.kd * derivative
        self._prev_error = error
        # For simplicity, let's assume the output is a valve position between 0 and 100
        return max(0, min(100, output))
