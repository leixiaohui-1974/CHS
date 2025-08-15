import unittest
from unittest.mock import MagicMock
from water_system_sdk.src.chs_sdk.agents.body_agents import PumpAgent
from water_system_sdk.src.chs_sdk.agents.message import Message

class TestPumpAgent(unittest.TestCase):

    def setUp(self):
        """
        Set up a mock kernel and a PumpAgent for testing.
        """
        self.kernel = MagicMock()
        self.kernel.message_bus = MagicMock()
        self.kernel.current_time = 0

        self.pump_agent = PumpAgent(
            agent_id="pump1",
            kernel=self.kernel,
            num_pumps_total=3,
            curve_coeffs=[-0.01, 0.1, 5.0],
            inlet_pressure_topic="pressure/inlet",
            outlet_pressure_topic="pressure/outlet",
            num_pumps_on_topic="pump/pump1/num_on",
            state_topic="pump/pump1/state"
        )
        self.pump_agent.setup()

    def test_initial_state(self):
        """
        Test that the pump agent starts in the StoppedState.
        """
        self.assertEqual(self.pump_agent.state_machine.current_state.__class__.__name__, 'PumpStoppedState')
        self.assertEqual(self.pump_agent.num_pumps_on, 0)

    def test_start_stop_cycle(self):
        """
        Test the transition from Stopped -> Starting -> Running -> Stopped.
        """
        # Initial state is Stopped
        self.assertEqual(self.pump_agent.state_machine.current_state.__class__.__name__, 'PumpStoppedState')

        # Send start command
        start_message = Message(topic="cmd.pump.start", sender_id="system", payload={})
        self.pump_agent.on_message(start_message)
        self.assertEqual(self.pump_agent.state_machine.current_state.__class__.__name__, 'PumpStartingState')

        # Execute for a few seconds to simulate startup time
        self.kernel.current_time = 3
        self.pump_agent.execute(self.kernel.current_time)
        self.assertEqual(self.pump_agent.state_machine.current_state.__class__.__name__, 'PumpStartingState')

        # Execute past the startup time to transition to Running
        self.kernel.current_time = 6
        self.pump_agent.execute(self.kernel.current_time)
        self.assertEqual(self.pump_agent.state_machine.current_state.__class__.__name__, 'PumpRunningState')
        self.assertEqual(self.pump_agent.num_pumps_on, 1) # Default target is 1

        # Send stop command
        stop_message = Message(topic="cmd.pump.stop", sender_id="system", payload={})
        self.pump_agent.on_message(stop_message)
        self.assertEqual(self.pump_agent.state_machine.current_state.__class__.__name__, 'PumpStoppedState')
        self.assertEqual(self.pump_agent.num_pumps_on, 0)

    def test_fault_state(self):
        """
        Test transitioning to and from the FaultState.
        """
        # Go to running state first
        start_message = Message(topic="cmd.pump.start", sender_id="system", payload={})
        self.pump_agent.on_message(start_message)
        self.kernel.current_time = 6
        self.pump_agent.execute(self.kernel.current_time)
        self.assertEqual(self.pump_agent.state_machine.current_state.__class__.__name__, 'PumpRunningState')

        # Send fault command
        fault_message = Message(topic="cmd.pump.fault", sender_id="system", payload={})
        self.pump_agent.on_message(fault_message)
        self.assertEqual(self.pump_agent.state_machine.current_state.__class__.__name__, 'PumpFaultState')
        self.assertEqual(self.pump_agent.num_pumps_on, 0)

        # Try to start while in fault state (should be ignored)
        start_message = Message(topic="cmd.pump.start", sender_id="system", payload={})
        self.pump_agent.on_message(start_message)
        self.assertEqual(self.pump_agent.state_machine.current_state.__class__.__name__, 'PumpFaultState')

        # Send reset command
        reset_message = Message(topic="cmd.pump.reset", sender_id="system", payload={})
        self.pump_agent.on_message(reset_message)
        self.assertEqual(self.pump_agent.state_machine.current_state.__class__.__name__, 'PumpStoppedState')

    def test_change_num_pumps_in_running_state(self):
        """
        Test changing the number of active pumps while in the RunningState.
        """
        # Go to running state
        self.pump_agent.transition_to('PumpRunningState')
        self.assertEqual(self.pump_agent.num_pumps_on, 1)

        # Change number of pumps
        num_pumps_message = Message(topic=self.pump_agent.num_pumps_on_topic, sender_id="system", payload={"value": 2})
        self.pump_agent.on_message(num_pumps_message)
        self.assertEqual(self.pump_agent.num_pumps_on, 2)
        self.assertEqual(self.pump_agent.target_num_pumps, 2)

if __name__ == '__main__':
    unittest.main()
