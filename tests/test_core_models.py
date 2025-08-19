import unittest
import sys
import os
import numpy as np

# Add the parent directory to the path to allow imports from chs_sdk
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from water_system_sdk.src.chs_sdk.modules.modeling.storage_models import LinearTank, MuskingumChannelModel

class TestCoreModels(unittest.TestCase):

    def test_linear_tank_mass_balance(self):
        """
        Tests the LinearTank model for correct mass balance calculation.
        """
        # 1. Setup
        initial_level = 10.0  # m
        area = 1000.0  # m^2
        inflow = 10.0  # m^3/s
        release_outflow = 2.0  # m^3/s
        demand_outflow = 3.0  # m^3/s
        dt = 60.0  # s

        # 2. Instantiate the model
        tank = LinearTank(area=area, initial_level=initial_level)

        # 3. Set inputs
        tank.input.inflow = inflow
        tank.input.release_outflow = release_outflow
        tank.input.demand_outflow = demand_outflow

        # 4. Run one step
        tank.step(dt=dt)

        # 5. Calculate expected result
        net_inflow = inflow - (release_outflow + demand_outflow)  # 10 - 5 = 5 m^3/s
        volume_change = net_inflow * dt  # 5 m^3/s * 60 s = 300 m^3
        level_change = volume_change / area  # 300 m^3 / 1000 m^2 = 0.3 m
        expected_final_level = initial_level + level_change  # 10.0 + 0.3 = 10.3 m

        # 6. Assert
        self.assertAlmostEqual(
            expected_final_level,
            tank.level,
            places=5,
            msg="LinearTank did not conserve mass correctly."
        )

    def test_muskingum_channel_routing(self):
        """
        Tests the MuskingumChannelModel for correct routing calculation.
        """
        # 1. Setup parameters
        K = 2.0  # hours
        x = 0.2
        dt = 1.0  # hours
        initial_inflow = 10.0  # m^3/s
        initial_outflow = 10.0  # m^3/s

        # 2. Manual calculation of coefficients
        denominator = K - K * x + 0.5 * dt  # 2 - 2*0.2 + 0.5*1 = 2 - 0.4 + 0.5 = 2.1
        C1 = (0.5 * dt - K * x) / denominator  # (0.5*1 - 2*0.2) / 2.1 = 0.1 / 2.1
        C2 = (0.5 * dt + K * x) / denominator  # (0.5*1 + 2*0.2) / 2.1 = 0.9 / 2.1
        C3 = (K - K * x - 0.5 * dt) / denominator  # (2 - 2*0.2 - 0.5*1) / 2.1 = 1.1 / 2.1

        expected_C1 = 0.1 / 2.1
        expected_C2 = 0.9 / 2.1
        expected_C3 = 1.1 / 2.1

        # 3. Instantiate the model
        model = MuskingumChannelModel(
            K=K, x=x, dt=dt,
            initial_inflow=initial_inflow,
            initial_outflow=initial_outflow
        )

        # 4. Assert that the model's coefficients are correct
        self.assertAlmostEqual(expected_C1, model.C1, places=7)
        self.assertAlmostEqual(expected_C2, model.C2, places=7)
        self.assertAlmostEqual(expected_C3, model.C3, places=7)

        # 5. Run a step
        new_inflow = 12.0 # m^3/s
        model.input.inflow = new_inflow

        # 6. Calculate expected outflow for this step
        # O_t = C1*I_t + C2*I_{t-1} + C3*O_{t-1}
        expected_outflow = (expected_C1 * new_inflow +
                            expected_C2 * initial_inflow +
                            expected_C3 * initial_outflow)

        # 7. Run the model's step method
        actual_outflow = model.step()

        # 8. Assert the output is correct
        self.assertAlmostEqual(expected_outflow, actual_outflow, places=7,
                               msg="Muskingum model did not route the flow correctly.")
