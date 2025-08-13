import unittest
import math

# Update imports to the new locations and interfaces
from water_system_simulator.modeling.hydrology.runoff_models import RunoffCoefficientModel, XinanjiangModel, SCSRunoffModel
from water_system_simulator.modeling.hydrology.routing_models import MuskingumModel

class TestHydrologyStrategies(unittest.TestCase):

    def test_runoff_coefficient_model(self):
        """Tests the RunoffCoefficientModel strategy."""
        model = RunoffCoefficientModel()
        sub_basin_params = {"C": 0.4}
        rainfall = 10.0
        dt = 1.0

        expected_runoff = rainfall * sub_basin_params["C"]
        calculated_runoff = model.calculate_runoff(rainfall, sub_basin_params, dt)
        self.assertAlmostEqual(calculated_runoff, expected_runoff, places=5)

    def test_xinanjiang_model_runoff_generation(self):
        """Tests the XinanjiangModel strategy."""
        # WM is needed for initial state calculation
        model = XinanjiangModel(params={"WM": 100.0}, states={"initial_W": 50.0})

        sub_basin_params = {
            "WM": 100.0,
            "B": 0.3,
            "evaporation": 5.0 # Evaporation rate in mm/hr
        }
        dt = 1.0

        # --- Test Case 1: Evaporation only ---
        rainfall = 0.0
        runoff = model.calculate_runoff(rainfall, sub_basin_params, dt)
        # Expected new moisture: W_new = W_old - E_rate * dt * (W/WM) = 50 - 5*1 * (50/100) = 47.5
        self.assertEqual(runoff, 0.0)
        self.assertAlmostEqual(model.W, 47.5, places=5)

    def test_scs_runoff_model(self):
        """Tests the SCSRunoffModel strategy."""
        model = SCSRunoffModel()
        sub_basin_params = {"CN": 75}
        # P > Ia, where Ia = 0.2S and S = (1000/75) - 10 = 3.33, Ia = 0.666
        rainfall = 10.0
        dt = 1.0

        s = (1000 / 75) - 10
        ia = 0.2 * s
        expected_runoff = ((rainfall - ia) ** 2) / (rainfall - ia + s)

        calculated_runoff = model.calculate_runoff(rainfall, sub_basin_params, dt)
        self.assertAlmostEqual(calculated_runoff, expected_runoff, places=5)

    def test_muskingum_routing_model(self):
        """Tests the MuskingumModel routing strategy."""
        model = MuskingumModel(states={"initial_inflow": 10.0, "initial_outflow": 10.0})

        sub_basin_params = {
            "area": 10.0, # km^2
            "K": 12.0,
            "x": 0.2
        }
        effective_rainfall = 5.0 # mm
        dt = 1.0 # hour

        # Expected inflow = (5 mm * 10 km^2 * 1000) / (1 hr * 3600 s/hr) = 13.888 m^3/s
        inflow = (effective_rainfall * sub_basin_params["area"] * 1000) / (dt * 3600)

        # Calculate expected outflow
        K, x = sub_basin_params["K"], sub_basin_params["x"]
        I_prev, O_prev = 10.0, 10.0
        I_t = inflow

        denominator = 2 * K * (1 - x) + dt
        C1 = (dt - 2 * K * x) / denominator
        C2 = (dt + 2 * K * x) / denominator
        C3 = (2 * K * (1 - x) - dt) / denominator

        expected_outflow = C1 * I_t + C2 * I_prev + C3 * O_prev

        calculated_outflow = model.route_flow(effective_rainfall, sub_basin_params, dt)
        self.assertAlmostEqual(calculated_outflow, expected_outflow, places=5)


if __name__ == '__main__':
    unittest.main()
