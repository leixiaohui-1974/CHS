import unittest
import numpy as np
import pandas as pd

# Add the src directory to the Python path
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'water_system_sdk', 'src')))

from water_system_simulator.modeling.integral_plus_delay_model import IntegralPlusDelayModel
from water_system_simulator.tools.identification_toolkit import identify_at_point, generate_model_bank

class TestIdentificationToolkit(unittest.TestCase):

    def test_integral_plus_delay_model(self):
        """
        Tests the basic functionality of the IntegralPlusDelayModel.
        """
        model = IntegralPlusDelayModel(K=0.1, T=2.0, dt=1.0, initial_value=10.0)

        # Initial state
        self.assertEqual(model.state.output, 10.0)

        # Step 1: input is 10, delayed input is 10
        model.input.inflow = 10.0
        model.step()
        # y(1) = y(0) + K * u(1-2) * dt = 10.0 + 0.1 * 10.0 * 1.0 = 11.0
        self.assertAlmostEqual(model.state.output, 11.0)

        # Step 2: input is 20, delayed input is 10
        model.input.inflow = 20.0
        model.step()
        # y(2) = y(1) + K * u(2-2) * dt = 11.0 + 0.1 * 10.0 * 1.0 = 12.0
        self.assertAlmostEqual(model.state.output, 12.0)

        # Step 3: input is 20, delayed input is 10 (from step 1)
        model.step()
        # y(3) = y(2) + K * u(3-2) * dt = 12.0 + 0.1 * 10.0 * 1.0 = 13.0
        self.assertAlmostEqual(model.state.output, 13.0)

    def test_identify_at_point_structure(self):
        """
        Tests the basic structure and API of identify_at_point.
        Since it uses dummy data, this is just a smoke test.
        """
        base_config = {
            "components": {
                "StVenantModel": {
                    "type": "StVenantModel",
                    "properties": {
                        "nodes_data": [{'name': 'UpstreamSource', 'type': 'inflow'}],
                        "reaches_data": []
                    }
                }
            }
        }
        operating_point = {'upstream_flow': 100.0}
        tasks = [{"model_type": "Muskingum", "input": "a", "output": "b"}]

        # This will use the dummy implementation inside the function
        results = identify_at_point(base_config, operating_point, tasks)

        self.assertIn("Muskingum_a_b", results)
        self.assertIn("K", results["Muskingum_a_b"])
        self.assertIn("X", results["Muskingum_a_b"])

    def test_generate_model_bank_structure(self):
        """
        Tests the basic structure and API of generate_model_bank.
        Since it uses dummy data, this is just a smoke test.
        """
        base_config = {}
        operating_space = [{'flow': 100, 'level': 10}, {'flow': 200, 'level': 11}]
        task = {"model_type": "Muskingum", "input": "a", "output": "b"}

        # Dummy validation data
        time = np.arange(0, 10)
        dummy_hydrograph = pd.DataFrame({'time': time, 'flow': time})

        model_bank = generate_model_bank(
            base_config, operating_space, task,
            dummy_hydrograph, dummy_hydrograph,
            target_accuracy=0.9
        )

        self.assertIsInstance(model_bank, list)
        self.assertTrue(len(model_bank) > 0)
        self.assertIn("condition_variable", model_bank[0])
        self.assertIn("max_value", model_bank[0])
        self.assertIn("parameters", model_bank[0])
        self.assertIn("K", model_bank[0]['parameters'])

if __name__ == '__main__':
    unittest.main()
