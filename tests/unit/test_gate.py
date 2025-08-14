import unittest
import numpy as np
from water_system_simulator.modeling.control_structure_models import GateModel

class TestGateModel(unittest.TestCase):

    def setUp(self):
        """Set up a standard gate model for reuse in tests."""
        self.gate_params = {
            "num_gates": 2,
            "gate_width": 1.5,
            "discharge_coeff": 0.6
        }
        self.gate_model = GateModel(**self.gate_params)
        self.g = 9.81

    def test_gate_free_flow_calculation(self):
        """
        Tests the flow calculation for the GateModel under free-flow conditions.
        """
        upstream_level = 10.0
        downstream_level = 0.2  # Lower than gate opening
        gate_opening = 0.5

        # Ensure it's a free-flow condition
        self.assertLess(downstream_level, gate_opening)

        self.gate_model.step(
            upstream_level=upstream_level,
            downstream_level=downstream_level,
            gate_opening=gate_opening
        )
        calculated_flow = self.gate_model.flow

        # Expected flow for FREE-FLOW
        area_per_gate = self.gate_params["gate_width"] * gate_opening
        flow_per_gate = self.gate_params["discharge_coeff"] * area_per_gate * np.sqrt(2 * self.g * upstream_level)
        expected_flow = flow_per_gate * self.gate_params["num_gates"]

        self.assertAlmostEqual(calculated_flow, expected_flow, places=5)

    def test_gate_submerged_flow_calculation(self):
        """
        Tests the flow calculation for the GateModel under submerged-flow conditions.
        """
        upstream_level = 10.0
        downstream_level = 1.0  # Higher than gate opening
        gate_opening = 0.5

        # Ensure it's a submerged-flow condition
        self.assertGreater(downstream_level, gate_opening)

        self.gate_model.step(
            upstream_level=upstream_level,
            downstream_level=downstream_level,
            gate_opening=gate_opening
        )
        calculated_flow = self.gate_model.flow

        # Expected flow for SUBMERGED-FLOW
        effective_head = upstream_level - downstream_level
        area_per_gate = self.gate_params["gate_width"] * gate_opening
        flow_per_gate = self.gate_params["discharge_coeff"] * area_per_gate * np.sqrt(2 * self.g * effective_head)
        expected_flow = flow_per_gate * self.gate_params["num_gates"]

        self.assertAlmostEqual(calculated_flow, expected_flow, places=5)

    def test_flow_zero_conditions(self):
        """
        Tests that flow is zero under various boundary conditions.
        """
        # Test with zero gate opening
        self.gate_model.step(upstream_level=10.0, downstream_level=2.0, gate_opening=0)
        self.assertEqual(self.gate_model.flow, 0.0)

        # Test with negative gate opening (should be clipped to 0)
        self.gate_model.step(upstream_level=10.0, downstream_level=2.0, gate_opening=-0.5)
        self.assertEqual(self.gate_model.flow, 0.0)

        # Test with upstream level equal to downstream level
        self.gate_model.step(upstream_level=5.0, downstream_level=5.0, gate_opening=0.5)
        self.assertEqual(self.gate_model.flow, 0.0)

        # Test with upstream level less than downstream level
        self.gate_model.step(upstream_level=4.0, downstream_level=5.0, gate_opening=0.5)
        self.assertEqual(self.gate_model.flow, 0.0)

if __name__ == '__main__':
    unittest.main()
