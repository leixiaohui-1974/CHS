import unittest
import pandas as pd
from water_system_simulator.modeling.base_model import BaseModel
from water_system_simulator.modeling.base_physical_entity import BasePhysicalEntity
from water_system_simulator.simulation_manager import SimulationManager
from water_system_simulator.core.simulation_modes import SimulationMode

# --- Mock Models for Testing ---

class MockSteadyModel(BaseModel):
    def __init__(self, **kwargs):
        super().__init__()
        self.called = False
        self.output = 1.0

    def solve(self, **kwargs):
        self.called = True

    def step(self, **kwargs):
        # This should not be called for a steady model
        pass

    def get_state(self):
        return {"state": "steady"}

class MockDynamicModel(BaseModel):
    def __init__(self, **kwargs):
        super().__init__()
        self.called = False
        self.output = 2.0

    def step(self, **kwargs):
        self.called = True

    def get_state(self):
        return {"state": "dynamic"}

class MockPrecisionModel(BaseModel):
    def __init__(self, **kwargs):
        super().__init__()
        self.called = False
        self.output = 3.0

    def step(self, **kwargs):
        self.called = True

    def get_state(self):
        return {"state": "precision"}

# --- Test Case ---

class TestArchitecture(unittest.TestCase):
    def setUp(self):
        """Set up the test environment."""
        self.sm = SimulationManager()
        # We need to import the registry to modify it for the test
        from water_system_simulator.simulation_manager import ComponentRegistry

        # Add mock models and the entity to the registry for this test
        ComponentRegistry._CLASS_MAP['MockSteadyModel'] = f"{__name__}.MockSteadyModel"
        ComponentRegistry._CLASS_MAP['MockDynamicModel'] = f"{__name__}.MockDynamicModel"
        ComponentRegistry._CLASS_MAP['MockPrecisionModel'] = f"{__name__}.MockPrecisionModel"
        # The BasePhysicalEntity is already in the map, but we ensure it's correct for the test's context
        ComponentRegistry._CLASS_MAP['BasePhysicalEntity'] = "water_system_simulator.modeling.base_physical_entity.BasePhysicalEntity"

        self.config = {
            "components": {
                "test_entity": {
                    "type": "BasePhysicalEntity",
                    "params": {},
                    "steady_model": {
                        "type": "MockSteadyModel",
                        "params": {}
                    },
                    "dynamic_model": {
                        "type": "MockDynamicModel",
                        "params": {}
                    },
                    "precision_model": {
                        "type": "MockPrecisionModel",
                        "params": {}
                    }
                }
            },
            "simulation_params": {"total_time": 2, "dt": 1},
            "execution_order": ["test_entity"],
            "logger_config": ["test_entity.output"]
        }

    def test_entity_model_delegation(self):
        """
        Tests that the SimulationManager correctly builds a PhysicalEntity
        and that the entity correctly delegates calls to the appropriate model
        based on the simulation mode.
        """
        # --- Test DYNAMIC mode ---
        results_dyn = self.sm.run(self.config, mode="DYNAMIC")
        entity_dyn = self.sm.components["test_entity"]

        self.assertIsInstance(entity_dyn, BasePhysicalEntity)
        self.assertTrue(entity_dyn.dynamic_model.called, "Dynamic model should have been called")
        self.assertFalse(entity_dyn.steady_model.called, "Steady model should NOT have been called in DYNAMIC mode")
        self.assertFalse(entity_dyn.precision_model.called, "Precision model should NOT have been called in DYNAMIC mode")
        self.assertEqual(entity_dyn.output, 2.0)
        self.assertEqual(results_dyn['test_entity.output'].iloc[-1], 2.0)

        # --- Test STEADY mode ---
        # Reset called flags
        entity_dyn.steady_model.called = False
        entity_dyn.dynamic_model.called = False
        entity_dyn.precision_model.called = False

        results_std = self.sm.run(self.config, mode="STEADY")
        entity_std = self.sm.components["test_entity"]

        self.assertTrue(entity_std.steady_model.called, "Steady model should have been called")
        self.assertFalse(entity_std.dynamic_model.called, "Dynamic model should NOT have been called in STEADY mode")
        self.assertFalse(entity_std.precision_model.called, "Precision model should NOT have been called in STEADY mode")
        self.assertEqual(entity_std.output, 1.0)
        self.assertEqual(results_std.shape[0], 1, "Steady simulation should only have one time step")
        self.assertEqual(results_std['test_entity.output'].iloc[-1], 1.0)


        # --- Test PRECISION mode ---
        # Reset called flags
        entity_std.steady_model.called = False
        entity_std.dynamic_model.called = False
        entity_std.precision_model.called = False

        results_pre = self.sm.run(self.config, mode="PRECISION")
        entity_pre = self.sm.components["test_entity"]

        self.assertTrue(entity_pre.precision_model.called, "Precision model should have been called")
        self.assertFalse(entity_pre.steady_model.called, "Steady model should NOT have been called in PRECISION mode")
        self.assertFalse(entity_pre.dynamic_model.called, "Dynamic model should NOT have been called in PRECISION mode")
        self.assertEqual(entity_pre.output, 3.0)
        self.assertEqual(results_pre['test_entity.output'].iloc[-1], 3.0)

if __name__ == '__main__':
    unittest.main()
