import unittest
from water_system_simulator.modeling.storage_models import MuskingumChannelModel

class TestChannel(unittest.TestCase):

    def test_muskingum_routing(self):
        """
        Tests the flow routing calculation for the MuskingumChannelModel.
        O_t+1 = C1*I_t+1 + C2*I_t + C3*O_t
        """
        K = 12.0  # hours
        x = 0.2
        dt = 2.0  # hours
        initial_inflow = 10.0  # m^3/s
        initial_outflow = 10.0 # m^3/s

        # Instantiate the model
        channel = MuskingumChannelModel(
            name="test_channel",
            K=K,
            x=x,
            dt=dt,
            initial_inflow=initial_inflow,
            initial_outflow=initial_outflow
        )

        # --- Calculate expected values ---
        # Calculate Muskingum coefficients
        denominator = K - K * x + 0.5 * dt
        C1 = (0.5 * dt - K * x) / denominator
        C2 = (0.5 * dt + K * x) / denominator
        C3 = (K - K * x - 0.5 * dt) / denominator

        # New inflow at the current step (I_t+1)
        current_inflow = 15.0

        # Expected outflow for the current step (O_t+1)
        expected_outflow = (C1 * current_inflow +
                            C2 * initial_inflow +
                            C3 * initial_outflow)

        # --- Run one step in the model ---
        calculated_outflow = channel.step(inflow=current_inflow)

        # --- Assert ---
        self.assertAlmostEqual(calculated_outflow, expected_outflow, places=5)

        # --- Test another step to ensure state is updated correctly ---

        # The 'current_inflow' and 'calculated_outflow' from the last step
        # become the 'previous_inflow' and 'previous_outflow' for the next step.
        previous_inflow_step2 = current_inflow
        previous_outflow_step2 = calculated_outflow

        # New inflow for step 2
        current_inflow_step2 = 20.0

        # Expected outflow for step 2
        expected_outflow_step2 = (C1 * current_inflow_step2 +
                                  C2 * previous_inflow_step2 +
                                  C3 * previous_outflow_step2)

        # --- Run the second step ---
        calculated_outflow_step2 = channel.step(inflow=current_inflow_step2)

        # --- Assert for step 2 ---
        self.assertAlmostEqual(calculated_outflow_step2, expected_outflow_step2, places=5)


if __name__ == '__main__':
    unittest.main()
