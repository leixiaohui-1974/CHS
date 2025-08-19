import unittest
import sys
import os
import numpy as np

# Add the parent directory to the path to allow imports from chs_sdk
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from water_system_sdk.src.chs_sdk.modules.modeling.storage_models import LinearTank, MuskingumChannelModel, NonlinearTank
from water_system_sdk.src.chs_sdk.modules.modeling.hydrology.runoff_models import SCSRunoffModel

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

    def test_nonlinear_tank_mass_balance(self):
        """
        Tests the NonlinearTank model for correct mass balance and interpolation.
        """
        # 1. Setup
        # A simple curve where level 10m=1000m3, 20m=8000m3 (like a V-shape trough or pyramid)
        level_volume_curve = np.array([
            [10.0, 20.0, 30.0],  # levels (m)
            [1000.0, 8000.0, 27000.0]  # volumes (m^3)
        ])
        initial_level = 20.0

        inflow = 50.0  # m^3/s
        outflow = 10.0 # m^3/s
        dt = 60.0      # s

        # 2. Instantiate the model
        model = NonlinearTank(
            level_to_volume=level_volume_curve,
            initial_level=initial_level
        )

        # 3. Check initial state
        initial_volume = np.interp(initial_level, level_volume_curve[0], level_volume_curve[1])
        self.assertAlmostEqual(initial_volume, model.volume, places=5)

        # 4. Set inputs and run one step
        model.input.inflow = inflow
        model.input.release_outflow = outflow
        model.step(dt=dt)

        # 5. Calculate expected result
        net_inflow = inflow - outflow  # 40 m^3/s
        volume_change = net_inflow * dt  # 40 * 60 = 2400 m^3
        expected_final_volume = initial_volume + volume_change # 8000 + 2400 = 10400 m^3

        # Manually interpolate to find the expected level
        expected_final_level = np.interp(expected_final_volume, level_volume_curve[1], level_volume_curve[0])

        # 6. Assert final state
        self.assertAlmostEqual(
            expected_final_volume,
            model.volume,
            places=5,
            msg="NonlinearTank volume did not conserve mass correctly."
        )
        self.assertAlmostEqual(
            expected_final_level,
            model.level,
            places=5,
            msg="NonlinearTank level did not interpolate correctly."
        )

    def test_scs_runoff_model(self):
        """
        Tests the SCSRunoffModel for correct runoff calculation.
        """
        # 1. Setup
        model = SCSRunoffModel()
        cn = 80
        params = {"CN": cn}

        # 2. Manual calculation for verification
        s = (1000 / cn) - 10  # (1000 / 80) - 10 = 12.5 - 10 = 2.5
        ia = 0.2 * s          # 0.2 * 2.5 = 0.5

        # 3. Test Case 1: Rainfall is less than initial abstraction (no runoff)
        low_rainfall = 0.4
        runoff1 = model.calculate_runoff(rainfall=low_rainfall, sub_basin_params=params, dt=1)
        self.assertEqual(runoff1, 0, "Runoff should be 0 when rainfall < Ia")

        # 4. Test Case 2: Rainfall is greater than initial abstraction (runoff occurs)
        high_rainfall = 2.0

        # Manually calculate expected runoff
        expected_runoff = ((high_rainfall - ia) ** 2) / (high_rainfall - ia + s)
        # expected_runoff = (2.0 - 0.5)^2 / (2.0 - 0.5 + 2.5) = 1.5^2 / 4.0 = 2.25 / 4.0 = 0.5625

        runoff2 = model.calculate_runoff(rainfall=high_rainfall, sub_basin_params=params, dt=1)
        self.assertAlmostEqual(
            expected_runoff,
            runoff2,
            places=7,
            msg="SCS model calculation is incorrect for P > Ia"
        )
