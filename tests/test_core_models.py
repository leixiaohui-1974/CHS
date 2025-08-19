import unittest
import sys
import os
import numpy as np

# Add the parent directory to the path to allow imports from chs_sdk
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from water_system_sdk.src.chs_sdk.modules.modeling.storage_models import LinearTank

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
