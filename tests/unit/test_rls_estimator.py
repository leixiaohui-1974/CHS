import unittest
import numpy as np
from water_system_simulator.control.rls_estimator import RecursiveLeastSquaresAgent

class TestRecursiveLeastSquaresAgent(unittest.TestCase):

    def test_initialization(self):
        """
        Tests if the agent is initialized correctly.
        """
        initial_params = {'a1': 0.0, 'b1': 0.0}
        agent = RecursiveLeastSquaresAgent(initial_params=initial_params, forgetting_factor=0.99)

        self.assertEqual(agent.forgetting_factor, 0.99)
        self.assertEqual(len(agent.param_names), 2)
        self.assertTrue('a1' in agent.param_names)
        self.assertTrue('b1' in agent.param_names)
        self.assertEqual(agent.theta.shape, (2, 1))
        self.assertEqual(agent.P.shape, (2, 2))

        state = agent.get_state()
        self.assertIn('a1', state)
        self.assertIn('b1', state)
        self.assertEqual(state['a1'], 0.0)
        self.assertEqual(state['b1'], 0.0)

    def test_step_convergence(self):
        """
        Tests if the RLS algorithm converges to the true parameters of a known system.
        """
        # True parameters for the system: y(k) = 0.8*y(k-1) + 0.5*u(k-1)
        true_a1 = 0.8
        true_b1 = 0.5

        # Initial guesses for the agent
        initial_params = {'a1': 0.1, 'b1': 0.1}
        agent = RecursiveLeastSquaresAgent(initial_params=initial_params, forgetting_factor=0.98)

        # Generate some synthetic data
        num_steps = 100
        inflows = np.random.randn(num_steps)
        outflows = np.zeros(num_steps)

        # Simulate the true system to get outflow data
        # We need to provide the first outflow value
        outflows[0] = np.random.randn()
        for k in range(1, num_steps):
            prev_outflow = outflows[k-1]
            prev_inflow = inflows[k-1]
            outflows[k] = true_a1 * prev_outflow + true_b1 * prev_inflow + np.random.normal(0, 0.01) # Add some noise

        # Run the RLS agent on the synthetic data
        for k in range(num_steps):
            agent.step(inflow=inflows[k], observed_outflow=outflows[k])

        # Check if the estimated parameters are close to the true parameters
        final_params = agent.get_state()

        # After 100 steps, the estimates should be reasonably close.
        # We'll check for a tolerance of 0.1, which is quite loose but safe for a stochastic test.
        self.assertAlmostEqual(final_params['a1'], true_a1, delta=0.1)
        self.assertAlmostEqual(final_params['b1'], true_b1, delta=0.1)

if __name__ == '__main__':
    unittest.main()
