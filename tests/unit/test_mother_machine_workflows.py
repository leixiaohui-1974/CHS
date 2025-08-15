import unittest
import pandas as pd
import yaml

from chs_sdk.factory.mother_machine import MotherMachine

class TestMotherMachineWorkflows(unittest.TestCase):
    """
    Test suite for the new workflow capabilities of the MotherMachine.
    """

    def setUp(self):
        """
        Set up the test case.
        """
        self.mother_machine = MotherMachine()
        # Create sample data for a Muskingum model
        sample_data = {
            'time': range(100),
            'inflow': [10, 11, 12, 13, 14, 15, 14, 13, 12, 11] * 10,
            'outflow': [9, 9.5, 10.5, 11.5, 12.5, 13.5, 13, 12, 11, 10] * 10
        }
        self.sample_df = pd.DataFrame(sample_data)

    def test_design_body_agent_from_data_success(self):
        """
        Tests the successful creation of a body agent configuration from data.
        """
        agent_config = self.mother_machine.design_body_agent_from_data(
            agent_id="river_reach_1",
            data=self.sample_df,
            model_type="Muskingum",
            dt=1.0,
            initial_guess=[10.0, 0.2],  # Initial guess for K and X
            bounds=([1e-9, 0], [100, 0.49])  # Bounds for K and X in the format ([min_K, min_X], [max_K, max_X])
        )

        # 1. Check the high-level structure
        self.assertIn("id", agent_config)
        self.assertIn("class", agent_config)
        self.assertIn("params", agent_config)
        self.assertEqual(agent_config["id"], "river_reach_1")

        # 2. Check the parameters
        params = agent_config["params"]
        self.assertEqual(params["model_type"], "Muskingum")
        self.assertIn("identified_parameters", params)
        self.assertIn("initial_state", params)

        # 3. Check the identified parameters' structure
        identified_params = params["identified_parameters"]
        self.assertIn("K", identified_params)
        self.assertIn("X", identified_params)
        self.assertIsInstance(identified_params["K"], float)
        self.assertIsInstance(identified_params["X"], float)

        # 4. Check that the initial state was set correctly
        self.assertEqual(params["initial_state"]["outflow"], self.sample_df['outflow'].iloc[0])

    def test_run_workflow_dynamic_loading(self):
        """
        Tests that the run_workflow method can dynamically load and run a workflow.
        """
        context = {
            "data": self.sample_df,
            "model_type": "Muskingum",
            "dt": 1.0,
            "initial_guess": [10.0, 0.2],
            "bounds": ([1e-9, 0], [100, 0.49]) # Correct format for curve_fit
        }

        # This will fail if the dynamic import fails
        result = self.mother_machine.run_workflow("system_id_workflow", context)

        self.assertIn("status", result)
        self.assertEqual(result["status"], "success")
        self.assertIn("identified_parameters", result)
        self.assertIn("K", result["identified_parameters"])
        self.assertIn("X", result["identified_parameters"])

    def test_workflow_not_found(self):
        """
        Tests that an appropriate error is raised if the workflow is not found.
        """
        with self.assertRaises(ImportError):
            self.mother_machine.run_workflow("non_existent_workflow", {})

if __name__ == '__main__':
    unittest.main()
