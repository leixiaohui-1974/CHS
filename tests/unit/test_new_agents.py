import unittest
from unittest.mock import MagicMock, ANY

# Agent imports
from chs_sdk.agents.base_agent import BaseAgent
from chs_sdk.agents.message import Message
from chs_sdk.agents.control_agents import PIDAgent, MPCAgent
from chs_sdk.agents.body_agents import TankAgent, GateAgent, ValveAgent, HydropowerStationAgent, PipeAgent

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
        self.mock_kernel.message_bus.subscribe.assert_called_once_with(pid_agent, 'tank/level')

        # Simulate receiving a message and then executing
        # The new agent waits for a message to be initialized
        pid_agent.on_message(Message(topic='tank/level', sender_id='t1', payload={'level': 4.5}))
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
        self.mock_kernel.message_bus.subscribe.assert_any_call(gate_agent, 'tank/level')
        self.mock_kernel.message_bus.subscribe.assert_any_call(gate_agent, 'channel/level')
        self.mock_kernel.message_bus.subscribe.assert_any_call(gate_agent, 'pid/output')

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
            cv=10.0,
            subscribes_to=['control/output']
        )
        valve_agent.setup()

        # Verify subscriptions
        self.mock_kernel.message_bus.subscribe.assert_called_once_with(valve_agent, 'control/output')

        # Simulate receiving a message
        valve_agent.on_message(Message(topic='control/output', sender_id='pid1', payload={'value': 0.75}))
        self.assertEqual(valve_agent.opening, 0.75)

        # Verify execution and publication
        valve_agent.execute(current_time=0)
        self.mock_kernel.message_bus.publish.assert_called_once()
        args, kwargs = self.mock_kernel.message_bus.publish.call_args
        sent_message = args[0]
        self.assertEqual(sent_message.topic, 'state/valve/valve1')
        self.assertIn('opening', sent_message.payload)
        self.assertIn('flow', sent_message.payload)
        self.assertEqual(sent_message.payload['flow'], 7.5) # cv * opening = 10.0 * 0.75

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

    def test_hydropower_station_agent(self):
        """
        Test the implementation of the HydropowerStationAgent.
        """
        hydro_agent = HydropowerStationAgent(
            agent_id='hydro1',
            kernel=self.mock_kernel,
            max_flow_area=10.0,
            discharge_coeff=0.9,
            efficiency=0.85,
            upstream_topic='reservoir/level',
            downstream_topic='river/level',
            vane_opening_topic='control/vane',
            state_topic='hydro/state',
            release_topic='hydro/release'
        )
        hydro_agent.setup()

        # Verify subscriptions
        self.assertEqual(self.mock_kernel.message_bus.subscribe.call_count, 3)
        self.mock_kernel.message_bus.subscribe.assert_any_call(hydro_agent, 'reservoir/level')
        self.mock_kernel.message_bus.subscribe.assert_any_call(hydro_agent, 'river/level')
        self.mock_kernel.message_bus.subscribe.assert_any_call(hydro_agent, 'control/vane')

        # Simulate receiving messages
        hydro_agent.on_message(Message(topic='reservoir/level', sender_id='r1', payload={'level': 100.0}))
        hydro_agent.on_message(Message(topic='river/level', sender_id='c1', payload={'level': 80.0}))
        hydro_agent.on_message(Message(topic='control/vane', sender_id='p1', payload={'value': 0.7}))

        self.assertEqual(hydro_agent.upstream_level, 100.0)
        self.assertEqual(hydro_agent.downstream_level, 80.0)
        self.assertEqual(hydro_agent.vane_opening, 0.7)

        # Execute and check for published state
        hydro_agent.execute(current_time=0)

        # Should publish twice: once for its state, once for the release
        self.assertEqual(self.mock_kernel.message_bus.publish.call_count, 2)

        # Check the main state publication
        state_call = self.mock_kernel.message_bus.publish.call_args_list[0]
        sent_message_state = state_call[0][0]
        self.assertEqual(sent_message_state.topic, 'hydro/state')
        self.assertIn('flow', sent_message_state.payload)
        self.assertIn('power', sent_message_state.payload)
        self.assertGreater(sent_message_state.payload['flow'], 0)
        self.assertGreater(sent_message_state.payload['power'], 0)

        # Check the release flow publication
        release_call = self.mock_kernel.message_bus.publish.call_args_list[1]
        sent_message_release = release_call[0][0]
        self.assertEqual(sent_message_release.topic, 'hydro/release')
        self.assertIn('value', sent_message_release.payload)
        self.assertEqual(sent_message_release.payload['value'], sent_message_state.payload['flow'])

    def test_pipe_agent(self):
        """
        Test the implementation of the PipeAgent.
        """
        pipe_agent = PipeAgent(
            agent_id='pipe1',
            kernel=self.mock_kernel,
            length=1000.0,
            diameter=0.5,
            friction_factor=0.02,
            inlet_pressure_topic='node1/pressure',
            outlet_pressure_topic='node2/pressure',
            state_topic='pipe/state'
        )
        pipe_agent.setup()

        # Verify subscriptions
        self.assertEqual(self.mock_kernel.message_bus.subscribe.call_count, 2)
        self.mock_kernel.message_bus.subscribe.assert_any_call(pipe_agent, 'node1/pressure')
        self.mock_kernel.message_bus.subscribe.assert_any_call(pipe_agent, 'node2/pressure')

        # Simulate receiving messages
        pipe_agent.on_message(Message(topic='node1/pressure', sender_id='n1', payload={'pressure': 50.0}))
        pipe_agent.on_message(Message(topic='node2/pressure', sender_id='n2', payload={'pressure': 40.0}))

        self.assertEqual(pipe_agent.inlet_pressure, 50.0)
        self.assertEqual(pipe_agent.outlet_pressure, 40.0)

        # Execute and check for published state
        pipe_agent.execute(current_time=0)
        self.mock_kernel.message_bus.publish.assert_called_once_with(ANY)
        args, kwargs = self.mock_kernel.message_bus.publish.call_args
        sent_message = args[0]

        self.assertEqual(sent_message.topic, 'pipe/state')
        self.assertIn('flow', sent_message.payload)
        self.assertGreater(sent_message.payload['flow'], 0)



if __name__ == '__main__':
    unittest.main()
