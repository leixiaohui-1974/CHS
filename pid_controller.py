class PID:
    def __init__(self, Kp, Ki, Kd, setpoint):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.integral = 0
        self.previous_error = 0

    def update(self, current_value, dt):
        error = self.setpoint - current_value

        # Proportional term
        P_out = self.Kp * error

        # Integral term
        self.integral += error * dt
        I_out = self.Ki * self.integral

        # Derivative term
        derivative = (error - self.previous_error) / dt
        D_out = self.Kd * derivative

        # Total output
        output = P_out + I_out + D_out

        # Update previous error
        self.previous_error = error

        return output
