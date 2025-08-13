import unittest
from src.water_system_simulator.control.pid_controller import PIDController

class TestPIDController(unittest.TestCase):

    def test_pid_calculation(self):
        """
        Tests the basic PID calculation without clamping.
        """
        pid = PIDController(kp=0.5, ki=0.2, kd=0.1, setpoint=10.0)

        # First step
        # error = 10 - 8 = 2
        # integral = 2 * 1 = 2
        # derivative = (2 - 0) / 1 = 2
        # output = 0.5 * 2 + 0.2 * 2 + 0.1 * 2 = 1.0 + 0.4 + 0.2 = 1.6
        output = pid.step(measured_value=8.0, dt=1.0)
        self.assertAlmostEqual(output, 1.6, places=5)
        self.assertAlmostEqual(pid.integral, 2.0, places=5)
        self.assertAlmostEqual(pid.previous_error, 2.0, places=5)

        # Second step
        # error = 10 - 9 = 1
        # integral = 2 + 1 * 1 = 3
        # derivative = (1 - 2) / 1 = -1
        # output = 0.5 * 1 + 0.2 * 3 + 0.1 * -1 = 0.5 + 0.6 - 0.1 = 1.0
        output = pid.step(measured_value=9.0, dt=1.0)
        self.assertAlmostEqual(output, 1.0, places=5)
        self.assertAlmostEqual(pid.integral, 3.0, places=5)
        self.assertAlmostEqual(pid.previous_error, 1.0, places=5)

    def test_output_clamping(self):
        """
        Tests that the output is correctly clamped.
        """
        pid = PIDController(kp=1.0, ki=1.0, kd=1.0, setpoint=10.0, output_min=0, output_max=5)

        # This step should produce a large output value that gets clamped
        # error = 10 - 0 = 10
        # integral = 10 * 1 = 10
        # derivative = 10 / 1 = 10
        # output = 1 * 10 + 1 * 10 + 1 * 10 = 30 -> clamped to 5
        output = pid.step(measured_value=0, dt=1.0)
        self.assertAlmostEqual(output, 5.0, places=5)

        # This step should produce a large negative output value that gets clamped
        pid = PIDController(kp=1.0, ki=1.0, kd=1.0, setpoint=10.0, output_min=-5, output_max=5)
        # error = 10 - 20 = -10
        # integral = -10 * 1 = -10
        # derivative = -10 / 1 = -10
        # output = 1*(-10) + 1*(-10) + 1*(-10) = -30 -> clamped to -5
        output = pid.step(measured_value=20.0, dt=1.0)
        self.assertAlmostEqual(output, -5.0, places=5)

if __name__ == '__main__':
    unittest.main()
