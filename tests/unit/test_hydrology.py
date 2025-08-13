import unittest
import math
from water_system_simulator.hydrology.models.runoff import RunoffCoefficientModel, XinanjiangModel

class TestHydrology(unittest.TestCase):

    def test_runoff_coefficient_model(self):
        """
        Tests the simple RunoffCoefficientModel.
        """
        params = {"C": 0.4}
        model = RunoffCoefficientModel(**params)

        precipitation = 10.0
        evaporation = 1.0 # This model doesn't use evaporation, but API requires it

        # Runoff should be a simple fraction of precipitation
        expected_runoff = precipitation * params["C"]
        calculated_runoff = model.calculate_pervious_runoff(
            pervious_precipitation=precipitation,
            evaporation=evaporation
        )

        self.assertAlmostEqual(calculated_runoff, expected_runoff, places=5)

        # Test zero precipitation
        calculated_runoff_zero = model.calculate_pervious_runoff(
            pervious_precipitation=0,
            evaporation=evaporation
        )
        self.assertEqual(calculated_runoff_zero, 0.0)

    def test_xinanjiang_model_runoff_generation(self):
        """
        Tests the runoff generation logic of the XinanjiangModel by checking
        edge cases and intuitive scenarios.
        """
        params = {
            "WM": 100.0, # Soil moisture capacity
            "B": 0.3,    # Exponent of storage capacity curve
            "IM": 0.05,  # Impervious area fraction (not used in pervious calculation)
        }
        initial_W = 50.0 # Initial soil moisture

        model = XinanjiangModel(**params, initial_states={"initial_W": initial_W})

        # --- Test Case 1: Evaporation only ---
        # Evaporation should reduce soil moisture when there's no rain.
        precip = 0.0
        evap = 5.0
        runoff = model.calculate_pervious_runoff(precip, evap)

        # Expected new moisture: W_new = W_old - E * (W/WM) = 50 - 5 * (50/100) = 47.5
        self.assertEqual(runoff, 0.0) # No runoff should occur
        self.assertAlmostEqual(model.W, 47.5, places=5)

        # --- Reset model for next test ---
        model.W = initial_W

        # --- Test Case 2: Saturating rainfall ---
        # A very large rainfall should fill the soil to capacity, and the rest becomes runoff.
        # Soil water capacity deficit = WM - W = 100 - 50 = 50.
        # Any rainfall above this should become runoff.
        precip = 80.0
        evap = 0.0

        # Expected runoff = P - (WM - W) = 80.0 - (100.0 - 50.0) = 30.0
        # This is because in the model, if P + A >= WMM, R = P - (WM - W)
        # With large P, P+A will surely be >= WMM.

        runoff = model.calculate_pervious_runoff(precip, evap)
        self.assertAlmostEqual(runoff, 30.0, places=5)

        # The soil should now be saturated.
        self.assertAlmostEqual(model.W, params["WM"], places=5)


if __name__ == '__main__':
    unittest.main()
