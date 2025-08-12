import unittest
import numpy as np

# Add project root to path to allow imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from modeling.storage_models import FirstOrderInertiaModel
from modeling.control_structure_models import GateModel

class TestModels(unittest.TestCase):

    def test_first_order_inertia_model(self):
        model = FirstOrderInertiaModel(initial_storage=100, time_constant=10)
        # With inflow = 10, outflow should approach 10 and storage should stabilize
        for _ in range(100):
            outflow = model.step(inflow=10)
        self.assertAlmostEqual(outflow, 10.0, delta=0.1)

    def test_gate_model(self):
        model = GateModel(discharge_coefficient=0.6, area=1.0)
        flow = model.calculate_flow(upstream_level=10, downstream_level=8)
        # Expected flow: 0.6 * 1.0 * sqrt(2 * 9.81 * 2) = 3.75
        self.assertAlmostEqual(flow, 3.75, delta=0.01)

if __name__ == '__main__':
    unittest.main()
