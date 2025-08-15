import unittest
import numpy as np
from water_system_sdk.src.water_system_simulator.agent.perception_agent import PerceptionAgent
from water_system_sdk.src.water_system_simulator.agent.body_agent import BodyAgent
from water_system_sdk.src.water_system_simulator.agent.control_agent import ControlAgent
from water_system_sdk.src.water_system_simulator.agent.dispatch_agent import DispatchAgent
from water_system_sdk.src.chs_sdk.agents.message import Message, MacroCommandMessage
from water_system_sdk.src.water_system_simulator.modeling.base_model import BaseModel

class MockModel(BaseModel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state = np.array([0.0])
    def step(self, dt, **kwargs):
        pass
    def get_state(self):
        return {"state": self.state}
    def get_state_vector(self):
        return self.state
    def set_state_from_vector(self, vector):
        self.state = vector
    def get_derivatives(self, t, y, **kwargs):
        return -y + kwargs.get("input", 0)

class TestNewAgentsV3(unittest.TestCase):

    def test_perception_agent_offline_id(self):
        import pandas as pd
        pa = PerceptionAgent(name="test_perception")
        mock_data = pd.DataFrame({
            "inflow": [1, 2, 3],
            "outflow": [0.5, 1.5, 2.5]
        })
        params = pa.execute_offline_identification(mock_data, strategy='Muskingum')
        self.assertIsNotNone(params)

    def test_body_agent_mode_switching(self):
        model = MockModel()
        ba = BodyAgent(name="test_body", core_physics_model=model, sensors={}, actuators={})
        self.assertEqual(ba.mode, "dynamic")
        ba.set_mode("steady_state")
        self.assertEqual(ba.mode, "steady_state")
        with self.assertRaises(ValueError):
            ba.set_mode("invalid_mode")

    def test_control_agent_algorithm_loading(self):
        ca = ControlAgent(name="test_control", control_algorithm="PID", algorithm_config={"Kp": 1, "Ki": 0, "Kd": 0, "set_point": 0})
        self.assertIsNotNone(ca.algorithm)
        self.assertEqual(ca.algorithm.Kp, 1)

    def test_dispatch_agent_command_generation(self):
        da = DispatchAgent(name="test_dispatch", control_agents=["pump1", "valve2"])
        commands = da.run_long_term_optimization()
        self.assertEqual(len(commands), 2)
        self.assertEqual(type(commands[0]["command"]).__name__, 'MacroCommandMessage')

    def test_dispatch_agent_emergency_response(self):
        da = DispatchAgent(name="test_dispatch")
        commands = da.trigger_emergency_response({"alarm": "high_pressure"})
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0]["command"].strategy, "immediate")

    def test_full_chain_placeholder(self):
        """
        This is a placeholder for a full integration test.
        A real test would involve a SimulationManager and a message bus.
        """
        # 1. Dispatcher sends a command
        dispatch = DispatchAgent(name="dispatch", control_agents=["control"])
        macro_commands = dispatch.run_long_term_optimization()

        # 2. Control agent receives the command
        control = ControlAgent(name="control", control_algorithm="PID", algorithm_config={"Kp": 1.0, "Ki": 0, "Kd": 0, "set_point": 0})
        control.on_message(macro_commands[0]['command'])
        self.assertIsNotNone(control.target_trajectory)

        # 3. Body agent is simulated
        model = MockModel()
        body = BodyAgent(name="body", core_physics_model=model, sensors={}, actuators={})

        # 4. Perception agent observes the body
        perception = PerceptionAgent(name="perception")

        # Simulate a few steps
        for _ in range(5):
            control.step(dt=1.0, current_state={"control": body.get_state_vector()[0]})
            # Here, the control command should be applied to the body
            body.step(dt=1.0, input=control.current_command)

        self.assertIsNotNone(control.current_command)
        print("Integration test placeholder passed.")

if __name__ == '__main__':
    unittest.main()
