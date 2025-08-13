import unittest
import numpy as np
from water_system_simulator.modeling.control_structure_models import GateStationModel

class TestGate(unittest.TestCase):

    def test_flow_calculation(self):
        """
        Tests the flow calculation for the GateStationModel.
        Flow = C * A * sqrt(2 * g * h)
        """
        num_gates = 2
        gate_width = 1.5  # m
        discharge_coeff = 0.6
        g = 9.81
        upstream_level = 10.0  # m
        gate_opening = 0.5  # m

        # Instantiate the model
        gate_station = GateStationModel(
            name="test_gate",
            num_gates=num_gates,
            gate_width=gate_width,
            discharge_coeff=discharge_coeff
        )

        # Run one step
        gate_station.step(upstream_level=upstream_level, gate_opening=gate_opening)
        calculated_flow = gate_station.flow

        # Calculate expected flow
        area_per_gate = gate_width * gate_opening
        flow_per_gate = discharge_coeff * area_per_gate * np.sqrt(2 * g * upstream_level)
        expected_flow = flow_per_gate * num_gates

        self.assertAlmostEqual(calculated_flow, expected_flow, places=5)

    def test_flow_zero_conditions(self):
        """
        Tests that flow is zero when upstream level or gate opening is zero.
        """
        gate_station = GateStationModel(
            name="test_gate_zero",
            num_gates=1,
            gate_width=2.0,
            discharge_coeff=0.6
        )

        # Test with zero upstream level
        gate_station.step(upstream_level=0, gate_opening=0.5)
        self.assertEqual(gate_station.flow, 0.0)

        # Test with zero gate opening
        gate_station.step(upstream_level=10.0, gate_opening=0)
        self.assertEqual(gate_station.flow, 0.0)

        # Test with negative gate opening (should be clipped to 0)
        gate_station.step(upstream_level=10.0, gate_opening=-0.5)
        self.assertEqual(gate_station.flow, 0.0)


if __name__ == '__main__':
    unittest.main()
