import unittest
import os
import sys

from chs_sdk.modules.hydrology.core import SubBasin

class TestCoreComponents(unittest.TestCase):

    def test_interception_model_reduces_runoff(self):
        """
        Tests if enabling the interception model correctly reduces the
        runoff calculated by the SubBasin class. This is a focused test
        to debug the persistent issue seen in full simulations.
        """
        # --- Parameters for a test SubBasin ---
        sub_basin_id = "TestBasin"
        area = 100.0  # km2

        # We use the simple RunoffCoefficientModel for this test
        params_no_interception = {
            "runoff_model": "RunoffCoefficient",
            "runoff_parameters": {"C": 0.5, "IM": 0.1},
            "human_activity_model": {"enabled": False}
        }

        params_with_interception = {
            "runoff_model": "RunoffCoefficient",
            "runoff_parameters": {"C": 0.5, "IM": 0.1},
            "human_activity_model": {
                "enabled": True,
                "parameters": {"initial_interception_capacity_mm": 10.0}
            }
        }

        # --- Create two SubBasin instances ---
        # One with interception, one without. They have their own independent states.
        subbasin_no_interception = SubBasin(sub_basin_id, area, params_no_interception)
        subbasin_with_interception = SubBasin(sub_basin_id, area, params_with_interception)

        # --- Test Data ---
        precipitation = 5.0  # mm
        evaporation = 1.0    # mm
        dt_hours = 1

        # --- Calculate runoff for both scenarios ---
        runoff_disabled = subbasin_no_interception.calculate_runoff(
            precipitation, evaporation, dt_hours
        )

        runoff_enabled = subbasin_with_interception.calculate_runoff(
            precipitation, evaporation, dt_hours
        )

        # --- Assertions ---
        # The runoff with the interception model enabled must be less than without it.
        self.assertLess(runoff_enabled, runoff_disabled)

        # Also check that some runoff is still produced (from the impervious area)
        self.assertGreater(runoff_enabled, 0)


if __name__ == '__main__':
    unittest.main()
