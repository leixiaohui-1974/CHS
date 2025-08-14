import unittest
from collections import defaultdict

# Temporarily add chs_sdk to path for testing
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from chs_sdk.agents.base import Message
from chs_sdk.agents.disturbance_agents import InflowAgent
from chs_sdk.agents.body_agents import TankAgent, GateAgent
from chs_sdk.agents.control_agents import PIDAgent


class SimpleMessageBus:
    """
    A simple in-memory message bus for testing purposes.
    """
    def __init__(self):
        self.subscriptions = defaultdict(list)
        self.message_queue = []

    def subscribe(self, topic, agent):
        self.subscriptions[topic].append(agent)

    def publish(self, message: Message):
        self.message_queue.append(message)

    def dispatch(self):
        while self.message_queue:
            message = self.message_queue.pop(0)
            if message.topic in self.subscriptions:
                for agent in self.subscriptions[message.topic]:
                    agent.on_message(message)


class TestAgentIntegration(unittest.TestCase):

    def test_inflow_tank_pid_gate_loop(self):
        """
        Tests a simple control loop with four agents:
        InflowAgent -> TankAgent -> PIDAgent -> GateAgent
        """
        bus = SimpleMessageBus()

        # 1. Create agents
        inflow_pattern = [10, 10, 10, 10, 10, 5, 5, 5, 5, 5]
        inflow_agent = InflowAgent(
            agent_id="inflow_1",
            message_bus=bus,
            rainfall_pattern=inflow_pattern,
            topic="tank/tank_1/inflow"
        )

        tank_agent = TankAgent(
            agent_id="tank_1",
            message_bus=bus,
            area=1000,
            initial_level=5.0
        )
        # The tank's state (level) is published to this topic
        pid_agent = PIDAgent(
            agent_id="pid_1",
            message_bus=bus,
            Kp=-0.5, Ki=-0.1, Kd=-0.01,
            set_point=10.0, # Target water level
            input_topic="tank/tank_1/state",
            output_topic="gate/gate_1/opening"
        )

        gate_agent = GateAgent(
            agent_id="gate_1",
            message_bus=bus,
            num_gates=1,
            gate_width=2,
            discharge_coeff=0.6
        )
        # The gate's calculated flow will act as the tank's release outflow
        gate_agent.subscribe("tank/tank_1/state") # for upstream_level

        # Manually connect gate outflow to tank outflow
        # In a real system, a dedicated agent or a configuration would handle this.
        class GateToTankConnector:
            def on_message(self, message: Message):
                if message.topic == "gate/gate_1/state":
                    flow = message.payload.get("flow", 0)
                    tank_agent.model.input.release_outflow = flow

        bus.subscribe("gate/gate_1/state", GateToTankConnector())


        # 2. Simulation Loop
        initial_tank_level = tank_agent.model.state.level
        print(f"Initial Tank Level: {initial_tank_level}")

        for t in range(10):
            print(f"\n--- Time Step {t} ---")

            # Agents perform their actions
            inflow_agent.execute()
            tank_agent.execute()
            pid_agent.execute()
            gate_agent.execute()

            # Dispatch all messages published in this step
            bus.dispatch()

            print(f"Tank Level: {tank_agent.model.state.level:.2f}")
            print(f"PID Output (Gate Opening): {pid_agent.controller.state.output:.2f}")
            print(f"Gate Flow: {gate_agent.model.flow:.2f}")

        final_tank_level = tank_agent.model.state.level
        print(f"\nFinal Tank Level: {final_tank_level}")

        # Assert that the system has changed from its initial state
        self.assertNotEqual(initial_tank_level, final_tank_level)
        # Assert that the tank level is approaching the setpoint
        self.assertTrue(5.0 < final_tank_level < 15.0)


if __name__ == '__main__':
    unittest.main()
