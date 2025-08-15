import unittest
import numpy as np

# Assuming the path to the SDK source is correctly set up in the environment
from water_system_sdk.src.water_system_simulator.control.pid_controller import PIDController
from water_system_sdk.src.water_system_simulator.control.mpc_controller import MPCController
from water_system_sdk.src.water_system_simulator.modeling.base_model import BaseModel
from water_system_sdk.src.water_system_simulator.core.datastructures import State, Input


# A simple, predictable model for testing the MPC controller
class SimpleLinearModel(BaseModel):
    """
    A simple linear model for testing: x[k+1] = A*x[k] + B*u[k] + C*d[k]
    Here, we use A=0.9, B=0.5, C=1.0
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state = State(output=0.0)
        self.input = Input(control_inflow=0.0, inflow=0.0)

    def step(self):
        # Update state based on linear model dynamics
        self.state.output = (0.9 * self.state.output +
                             0.5 * self.input.control_inflow +
                             1.0 * self.input.inflow)

    def get_state(self):
        return {'output': self.state.output}


class TestPIDController(unittest.TestCase):
    """
    Unit tests for the PIDController, which is the core of the PIDAgent.
    """

    def test_pid_components_and_output(self):
        """
        Tests the individual P, I, D components and the final output.
        """
        # 1. Setup the PID controller
        pid = PIDController(Kp=0.5, Ki=0.2, Kd=0.1, set_point=10.0)

        # 2. First step: with a current value of 8.0
        # Error = 10.0 - 8.0 = 2.0
        # P = 0.5 * 2.0 = 1.0
        # I = 0.2 * (0 + 2.0 * 1.0) = 0.4
        # D = 0.1 * (2.0 - 0) / 1.0 = 0.2
        # Output = 1.0 + 0.4 + 0.2 = 1.6
        output = pid.step(dt=1.0, error_source=8.0)
        self.assertAlmostEqual(output, 1.6, places=5)
        self.assertAlmostEqual(pid.state.integral, 2.0, places=5) # integral is error * dt
        self.assertAlmostEqual(pid.state.previous_error, 2.0, places=5)

        # 3. Second step: with a current value of 9.0
        # Error = 10.0 - 9.0 = 1.0
        # Previous Error = 2.0
        # P = 0.5 * 1.0 = 0.5
        # Integral term = 0.2 * (2.0 + 1.0 * 1.0) = 0.6
        # Derivative term = 0.1 * (1.0 - 2.0) / 1.0 = -0.1
        # Output = 0.5 + 0.6 - 0.1 = 1.0
        output = pid.step(dt=1.0, error_source=9.0)
        self.assertAlmostEqual(output, 1.0, places=5)
        self.assertAlmostEqual(pid.state.integral, 3.0, places=5) # integral is 2.0 + 1.0
        self.assertAlmostEqual(pid.state.previous_error, 1.0, places=5)

    def test_anti_windup_logic(self):
        """
        Tests that the integral term does not accumulate when the output is saturated.
        """
        # 1. Setup with tight output limits
        pid = PIDController(Kp=1.0, Ki=1.0, Kd=0.0, set_point=10.0, output_min=0, output_max=5)

        # 2. First step: High error, output should saturate
        # Error = 10 - 0 = 10
        # P = 1 * 10 = 10
        # I = 1 * (0 + 10 * 1) = 10
        # Unbounded output = 10 + 10 = 20
        # Clamped output = 5
        output = pid.step(dt=1.0, error_source=0.0)
        self.assertAlmostEqual(output, 5.0, places=5)

        # Since output was clamped (20 > 5), integral should NOT be updated.
        self.assertAlmostEqual(pid.state.integral, 0.0, places=5)

        # 3. Second step: Lower error, output should not saturate
        # Error = 10 - 6 = 4
        # P = 1 * 4 = 4
        # I = 1 * (0 + 4 * 1) = 4  (integral is still 0 from previous step)
        # Unbounded output = 4 + 4 = 8
        # Clamped output = 5
        output = pid.step(dt=1.0, error_source=6.0)
        self.assertAlmostEqual(output, 5.0, places=5)

        # Output was clamped again (8 > 5), integral should still be 0.
        self.assertAlmostEqual(pid.state.integral, 0.0, places=5)

        # 4. Third step: Error small enough to be in non-saturated range
        # Error = 10 - 8 = 2
        # P = 1 * 2 = 2
        # I = 1 * (0 + 2*1) = 2
        # Unbounded output = 2 + 2 = 4
        # Clamped output = 4
        output = pid.step(dt=1.0, error_source=8.0)
        self.assertAlmostEqual(output, 4.0, places=5)

        # Output was NOT clamped (4 < 5), so integral SHOULD be updated.
        self.assertAlmostEqual(pid.state.integral, 2.0, places=5)

if __name__ == '__main__':
    unittest.main()


class TestMPCController(unittest.TestCase):
    """
    Unit tests for the MPCController, which is the core of the MPCAgent.
    """

    def test_mpc_produces_reasonable_control(self):
        """
        Tests that the MPC controller generates a control action that moves the
        system towards the setpoint.
        """
        # 1. Setup the model and controller
        model = SimpleLinearModel()
        mpc = MPCController(
            prediction_model=model,
            prediction_horizon=5,
            control_horizon=2,
            set_point=10.0,
            q_weight=1.0,
            r_weight=0.1,
            u_min=-10.0,
            u_max=10.0
        )

        # 2. Set initial state and run one step
        # Current state is 0, setpoint is 10.
        # We expect a positive control action to increase the state.
        current_state = 0.0
        disturbance = np.zeros(5) # No disturbance
        control_action = mpc.step(current_state, disturbance)

        # 3. Assert that the control action is reasonable
        self.assertIsNotNone(control_action)
        self.assertGreater(control_action, 0, "Control action should be positive to reach the setpoint.")
        self.assertLessEqual(control_action, 10.0)

        # 4. Test again, but now the state is above the setpoint
        # Current state is 15, setpoint is 10.
        # We expect a negative control action to decrease the state.
        current_state = 15.0
        control_action = mpc.step(current_state, disturbance)
        self.assertIsNotNone(control_action)
        self.assertLess(control_action, 0, "Control action should be negative to reach the setpoint.")
        self.assertGreaterEqual(control_action, -10.0)
