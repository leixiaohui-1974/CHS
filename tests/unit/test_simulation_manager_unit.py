import unittest
import pandas as pd

# Adjust path to import SDK components
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'water_system_sdk', 'src')))

from water_system_simulator.simulation_manager import SimulationManager
from water_system_simulator.modeling.base_model import BaseModel

# A simple mock component for testing the manager
class MockComponent(BaseModel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.value = 10
        self.output = 0

    def multiply(self, factor):
        self.output = self.value * factor
        return self.output

    def step(self, dt, t):
        self.value += 1 # Just to have some state change

    def get_state(self):
        return {"value": self.value, "output": self.output}

class TestSimulationManager(unittest.TestCase):

    def setUp(self):
        self.manager = SimulationManager()

    def test_advanced_execution_order(self):
        """
        Tests that the SimulationManager can execute a dictionary-based
        instruction in the execution_order list.
        """
        config = {
            "simulation_params": { "total_time": 2, "dt": 1 },
            "components": {
                "source": { "type": "MockComponent", "params": { "value": 10 } },
                "target": { "type": "MockComponent", "params": {} }
            },
            "execution_order": [
                "source", # Standard step call
                {
                    "component": "target",
                    "method": "multiply",
                    "args": { "factor": "source.value" },
                    "result_to": "target.output"
                }
            ],
            "logger_config": ["source.value", "target.output"]
        }

        # Manually add the mock component to the registry for this test
        from water_system_simulator.simulation_manager import ComponentRegistry
        ComponentRegistry._CLASS_MAP['MockComponent'] = f"{__name__}.MockComponent"

        results_df = self.manager.run(config)

        # At t=0:
        # source.step() runs -> source.value becomes 11
        # target.multiply(factor=source.value=11) runs -> target.output becomes 110
        self.assertEqual(results_df.iloc[0]["source.value"], 11)
        self.assertEqual(results_df.iloc[0]["target.output"], 110)

        # At t=1:
        # source.step() runs -> source.value becomes 12
        # target.multiply(factor=source.value=12) runs. target.value is still 10.
        # So, target.output becomes 10 * 12 = 120.
        self.assertEqual(results_df.iloc[1]["source.value"], 12)
        self.assertEqual(results_df.iloc[1]["target.output"], 120)

        # Clean up the registry
        del ComponentRegistry._CLASS_MAP['MockComponent']

if __name__ == '__main__':
    unittest.main()
