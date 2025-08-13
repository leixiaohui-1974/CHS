import unittest
from water_system_simulator.control.pid_controller import PIDController

class TestPIDController(unittest.TestCase):

    def test_pid_calculation(self):
        """
        Tests the basic PID calculation without clamping.
        """
        pid = PIDController(Kp=0.5, Ki=0.2, Kd=0.1, set_point=10.0)

        # First step
        # error = 10 - 8 = 2
        # integral = 2 * 1 = 2
        # derivative = (2 - 0) / 1 = 2
        # output = 0.5 * 2 + 0.2 * 2 + 0.1 * 2 = 1.0 + 0.4 + 0.2 = 1.6
        pid.input.error_source = 8.0
        output = pid.step(dt=1.0)
        self.assertAlmostEqual(output, 1.6, places=5)
        self.assertAlmostEqual(pid.state.integral, 2.0, places=5)
        self.assertAlmostEqual(pid.state.previous_error, 2.0, places=5)

        # Second step
        # error = 10 - 9 = 1
        # integral = 2 + 1 * 1 = 3
        # derivative = (1 - 2) / 1 = -1
        # output = 0.5 * 1 + 0.2 * 3 + 0.1 * -1 = 0.5 + 0.6 - 0.1 = 1.0
        pid.input.error_source = 9.0
        output = pid.step(dt=1.0)
        self.assertAlmostEqual(output, 1.0, places=5)
        self.assertAlmostEqual(pid.state.integral, 3.0, places=5)
        self.assertAlmostEqual(pid.state.previous_error, 1.0, places=5)

    def test_pid_clamping(self):
        """
        Tests that the output is correctly clamped.
        """
        pid = PIDController(Kp=1.0, Ki=1.0, Kd=1.0, set_point=10.0, output_min=0, output_max=5)

        # This step should produce a large output value that gets clamped
        # error = 10 - 0 = 10
        # integral = 10 * 1 = 10
        # derivative = 10 / 1 = 10
        # output = 1 * 10 + 1 * 10 + 1 * 10 = 30 -> clamped to 5
        pid.input.error_source = 0.0
        output = pid.step(dt=1.0)
        self.assertAlmostEqual(output, 5.0, places=5)
        self.assertEqual(output, pid.output_max)

        # This step should produce a large negative output value that gets clamped
        pid.set_point = 0.0
        pid.input.error_source = 10.0
        output = pid.step(dt=1.0)
        self.assertAlmostEqual(output, 0.0, places=5)
        self.assertEqual(output, pid.output_min)

    def test_pid_anti_windup(self):
        """
        Tests the anti-windup mechanism.
        """
        pid = PIDController(Kp=1.0, Ki=1.0, Kd=0.0, set_point=10.0, output_min=-5, output_max=5)

        # First step, output is not saturated
        # error = 10 - 8 = 2
        # integral = 2 * 1 = 2
        # output = 1 * 2 + 1 * 2 = 4 -> not clamped
        pid.input.error_source = 8.0
        pid.step(dt=1.0)
        self.assertAlmostEqual(pid.state.integral, 2.0, places=5)

        # Second step, output should be saturated
        # error = 10 - 0 = 10
        # integral should remain 2.0 due to anti-windup
        # output = 1 * 10 + 1 * (2 + 10) = 22 -> clamped to 5
        pid.input.error_source = 0.0
        pid.step(dt=1.0)
        self.assertAlmostEqual(pid.state.integral, 2.0, places=5)

if __name__ == '__main__':
    unittest.main()
