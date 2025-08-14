import unittest
import numpy as np
from water_system_simulator.control.kf_estimator import ParameterKalmanFilterAgent

class TestParameterKalmanFilterAgent(unittest.TestCase):

    def test_initialization(self):
        """
        Tests if the KF agent is initialized correctly.
        """
        initial_params = {'a1': 0.1, 'b1': 0.2}
        agent = ParameterKalmanFilterAgent(
            initial_params=initial_params,
            process_noise_Q=0.0001,
            measurement_noise_R=0.01
        )

        self.assertEqual(len(agent.param_names), 2)
        self.assertEqual(agent.x.shape, (2, 1))
        self.assertEqual(agent.P.shape, (2, 2))
        self.assertEqual(agent.Q.shape, (2, 2))
        self.assertEqual(agent.Q[0, 0], 0.0001)
        self.assertEqual(agent.R, 0.01)

        state = agent.get_state()
        self.assertIn('a1', state)
        self.assertIn('b1', state)
        self.assertEqual(state['a1'], 0.1)
        self.assertEqual(state['b1'], 0.2)

    def test_step_convergence(self):
        """
        Tests if the KF parameter estimation algorithm converges.
        """
        # True parameters for the system: y(k) = 0.85*y(k-1) + 0.5*u(k-1)
        true_a1 = 0.85
        true_b1 = 0.5

        # Initial guesses for the agent
        initial_params = {'a1': 0.0, 'b1': 0.0}
        agent = ParameterKalmanFilterAgent(
            initial_params=initial_params,
            process_noise_Q=1e-5, # Small Q to allow adaptation
            measurement_noise_R=0.01**2 # R should be variance, so sigma^2
        )

        # Generate synthetic data
        num_steps = 150
        inflows = 5 * np.random.randn(num_steps)
        outflows = np.zeros(num_steps)

        # Simulate the true system
        outflows[0] = np.random.randn()
        for k in range(1, num_steps):
            prev_outflow = outflows[k-1]
            prev_inflow = inflows[k-1]
            # The true system dynamics + measurement noise
            outflows[k] = true_a1 * prev_outflow + true_b1 * prev_inflow + np.random.normal(0, 0.01)

        # Run the KF agent on the synthetic data
        for k in range(num_steps):
            agent.step(inflow=inflows[k], observed_outflow=outflows[k])

        # Check for convergence
        final_params = agent.get_state()

        # After enough steps, the estimates should be close to the true values.
        # The tolerance is kept relatively loose because of the stochastic nature of the test.
        self.assertAlmostEqual(final_params['a1'], true_a1, delta=0.15)
        self.assertAlmostEqual(final_params['b1'], true_b1, delta=0.15)

if __name__ == '__main__':
    unittest.main()
