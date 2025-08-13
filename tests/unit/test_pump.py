import unittest
import numpy as np
from water_system_simulator.modeling.control_structure_models import PumpStationModel

class TestPump(unittest.TestCase):

    def test_head_flow_curve(self):
        """
        Tests the head-flow curve calculation for the PumpStationModel.
        Flow = a*Head^2 + b*Head + c
        """
        # For Flow = a*H^2 + b*H + c
        curve_coeffs = [-0.01, 0.1, 5.0]
        num_pumps_on = 2
        inlet_pressure = 5.0  # m
        outlet_pressure = 20.0 # m

        # Instantiate the model
        pump_station = PumpStationModel(
            name="test_pump",
            num_pumps_total=3,
            curve_coeffs=curve_coeffs,
            initial_num_pumps_on=1
        )

        # Run one step
        pump_station.step(
            inlet_pressure=inlet_pressure,
            outlet_pressure=outlet_pressure,
            num_pumps_on=num_pumps_on
        )
        calculated_flow = pump_station.flow

        # Calculate expected flow
        head_diff = outlet_pressure - inlet_pressure
        a, b, c = curve_coeffs
        flow_per_pump = a * head_diff**2 + b * head_diff + c
        expected_flow = flow_per_pump * num_pumps_on

        self.assertAlmostEqual(calculated_flow, expected_flow, places=5)

    def test_flow_zero_conditions(self):
        """
        Tests that flow is zero when no pumps are on or head is too high.
        """
        curve_coeffs = [-0.01, 0.1, 5.0]
        pump_station = PumpStationModel(
            name="test_pump_zero",
            num_pumps_total=3,
            curve_coeffs=curve_coeffs
        )

        # Test with zero pumps on
        pump_station.step(inlet_pressure=5.0, outlet_pressure=20.0, num_pumps_on=0)
        self.assertEqual(pump_station.flow, 0.0)

        # Test with head difference that should result in zero or negative flow per pump
        # Flow = -0.01*H^2 + 0.1*H + 5. This quadratic has roots at H = ( -0.1 +- sqrt(0.1^2 - 4*-0.01*5) ) / (2 * -0.01)
        # H = (-0.1 +- sqrt(0.01 + 0.2)) / -0.02 = (-0.1 +- sqrt(0.21)) / -0.02
        # H = (-0.1 +- 0.458) / -0.02. Positive root is H = (-0.558)/-0.02 = 27.9
        # So any head > 27.9 should result in zero flow.
        high_head_diff = 30.0
        pump_station.step(inlet_pressure=5.0, outlet_pressure=5.0 + high_head_diff, num_pumps_on=1)
        self.assertEqual(pump_station.flow, 0.0)


if __name__ == '__main__':
    unittest.main()
