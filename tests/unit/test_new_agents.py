import unittest
from unittest.mock import MagicMock, ANY

# Agent imports
from chs_sdk.agents.base_agent import BaseAgent
from chs_sdk.agents.message import Message
from chs_sdk.agents.control_agents import PIDAgent, MPCAgent
from chs_sdk.agents.body_agents import TankAgent, GateAgent, ValveAgent

# Old model imports for creating agent instances
from water_system_sdk.src.water_system_simulator.modeling.storage_models import ReservoirModel

class TestNewAgentImplementation(unittest.TestCase):

    def setUp(self):
        """
        Set up a mock kernel and message bus for each test.
        """
        self.mock_kernel = MagicMock()
        self.mock_kernel.message_bus = MagicMock()
        # Simulate time_step attribute for agents that need it
        self.mock_kernel.time_step = 1.0

    def test_pid_agent_init_and_execute(self):
        """
        Test that the PIDAgent can be initialized and its execute method runs.
        """
        pid_agent = PIDAgent(
            agent_id='pid1',
            kernel=self.mock_kernel,
            Kp=1.0, Ki=0.1, Kd=0.01,
            set_point=5.0,
            input_topic='tank/level',
            output_topic='valve/opening'
        )
        pid_agent.setup()
        self.mock_kernel.message_bus.subscribe.assert_called_once_with('tank/level', pid_agent)

        # Simulate receiving a message and then executing
        pid_agent.current_value = 4.5
        pid_agent.execute(current_time=0)

        # Check if the agent published a message
        self.mock_kernel.message_bus.publish.assert_called_once()
        # Check the topic of the published message
        args, kwargs = self.mock_kernel.message_bus.publish.call_args
        sent_message = args[0]
        self.assertEqual(sent_message.topic, 'valve/opening')
        self.assertIn('value', sent_message.payload)

    def test_gate_agent_refactored_init_and_execute(self):
        """
        Test the refactored GateAgent to ensure its constructor and subscriptions are correct.
        """
        gate_agent = GateAgent(
            agent_id='gate1',
            kernel=self.mock_kernel,
            num_gates=1,
            gate_width=2.0,
            discharge_coeff=0.8,
            upstream_topic='tank/level',
            downstream_topic='channel/level',
            opening_topic='pid/output',
            state_topic='gate/state'
        )
        gate_agent.setup()

        # Verify it subscribed to all its input topics
        self.assertEqual(self.mock_kernel.message_bus.subscribe.call_count, 3)
        self.mock_kernel.message_bus.subscribe.assert_any_call('tank/level', gate_agent)
        self.mock_kernel.message_bus.subscribe.assert_any_call('channel/level', gate_agent)
        self.mock_kernel.message_bus.subscribe.assert_any_call('pid/output', gate_agent)

        # Simulate receiving messages
        gate_agent.on_message(Message(topic='tank/level', sender_id='t1', payload={'level': 10.0}))
        gate_agent.on_message(Message(topic='channel/level', sender_id='c1', payload={'level': 5.0}))
        gate_agent.on_message(Message(topic='pid/output', sender_id='p1', payload={'value': 0.5}))

        self.assertEqual(gate_agent.upstream_level, 10.0)
        self.assertEqual(gate_agent.downstream_level, 5.0)
        self.assertEqual(gate_agent.gate_opening, 0.5)

        # Execute and check for published state
        gate_agent.execute(current_time=0)
        self.mock_kernel.message_bus.publish.assert_called_once_with(ANY)
        args, kwargs = self.mock_kernel.message_bus.publish.call_args
        sent_message = args[0]
        self.assertEqual(sent_message.topic, 'gate/state')
        self.assertIn('flow', sent_message.payload)

    def test_valve_agent_standalone_implementation(self):
        """
        Test the standalone ValveAgent implementation.
        """
        valve_agent = ValveAgent(
            agent_id='valve1',
            kernel=self.mock_kernel,
            num_gates=1, # The model is a gate model
            gate_width=1.0,
            discharge_coeff=0.9,
            upstream_topic='tank/level',
            downstream_topic='pipe/pressure',
            opening_topic='control/output',
            state_topic='valve/state'
        )
        valve_agent.setup()

        # Verify subscriptions
        self.assertEqual(self.mock_kernel.message_bus.subscribe.call_count, 3)
        self.mock_kernel.message_bus.subscribe.assert_any_call('tank/level', valve_agent)

        # Verify execution and publication
        valve_agent.execute(current_time=0)
        self.mock_kernel.message_bus.publish.assert_called_once()
        args, kwargs = self.mock_kernel.message_bus.publish.call_args
        sent_message = args[0]
        self.assertEqual(sent_message.topic, 'valve/state')

    def test_mpc_agent_full_implementation(self):
        """
        Test the full implementation of the MPCAgent.
        This requires a mock prediction model.
        """
        # Create a mock prediction model that adheres to the BaseModel interface
        mock_prediction_model = MagicMock(spec=ReservoirModel)
        mock_prediction_model.get_state.return_value = {'output': 5.0}

        # The MPC controller's _linearize_model_at_point is complex, so we mock the controller itself
        # for a more focused unit test on the agent's behavior.
        mock_mpc_controller = MagicMock()
        mock_mpc_controller.step.return_value = 0.75 # Simulate a control action

        mpc_agent = MPCAgent(
            agent_id='mpc1',
            kernel=self.mock_kernel,
            prediction_model=mock_prediction_model,
            prediction_horizon=10,
            control_horizon=3,
            set_point=5.0,
            q_weight=1.0, r_weight=0.1,
            u_min=0.0, u_max=1.0,
            state_topic='tank/state',
            disturbance_topic='inflow/forecast',
            output_topic='valve/opening'
        )
        # Manually replace the agent's controller with our mock
        mpc_agent.controller = mock_mpc_controller
        mpc_agent.setup()

        # Verify subscriptions
        self.assertEqual(self.mock_kernel.message_bus.subscribe.call_count, 2)

        # Simulate receiving state and disturbance messages
        mpc_agent.on_message(Message(topic='tank/state', sender_id='t1', payload={'level': 4.8}))
        mpc_agent.on_message(Message(topic='inflow/forecast', sender_id='d1', payload={'forecast': [1, 1.1, 1.2]}))

        self.assertEqual(mpc_agent.current_state, 4.8)
        self.assertListEqual(list(mpc_agent.disturbance_forecast), [1, 1.1, 1.2])

        # Execute the agent
        mpc_agent.execute(current_time=0)

        # Verify that the controller's step method was called with the correct state
        mock_mpc_controller.step.assert_called_once()
        call_args = mock_mpc_controller.step.call_args[1]
        self.assertEqual(call_args['current_state'], 4.8)
        self.assertTrue(all(call_args['disturbance_forecast'] == [1, 1.1, 1.2]))

        # Verify that the agent published the result from the controller
        self.mock_kernel.message_bus.publish.assert_called_once()
        args, kwargs = self.mock_kernel.message_bus.publish.call_args
        sent_message = args[0]
        self.assertEqual(sent_message.topic, 'valve/opening')
        self.assertEqual(sent_message.payload['value'], 0.75)


if __name__ == '__main__':
    unittest.main()
