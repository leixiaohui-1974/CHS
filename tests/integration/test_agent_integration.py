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

    def subscribe(self, agent, topic):
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
        from unittest.mock import MagicMock
        mock_kernel = MagicMock()
        mock_kernel.message_bus = bus
        mock_kernel.time_step = 1.0

        inflow_agent = InflowAgent(
            agent_id="inflow_1",
            kernel=mock_kernel,
            rainfall_pattern=inflow_pattern,
            topic="data.inflow/tank_1"
        )

        tank_agent = TankAgent(
            agent_id="tank_1",
            kernel=mock_kernel,
            area=1000,
            initial_level=5.0,
            subscribes_to=["data.inflow/tank_1"]
        )
        # The tank's state (level) is published to this topic
        pid_agent = PIDAgent(
            agent_id="pid_1",
            kernel=mock_kernel,
            Kp=0.5, Ki=0.1, Kd=0.01,
            set_point=10.0, # Target water level
            subscribes_to=["dummy_macro_topic", "tank/tank_1/state"],
            publishes_to="gate/gate_1/opening",
            output_min=0,
            output_max=1
        )

        gate_agent = GateAgent(
            agent_id="gate_1",
            kernel=mock_kernel,
            num_gates=1,
            gate_width=2,
            discharge_coeff=0.6,
            upstream_topic="tank/tank_1/state",
            downstream_topic="dummy_downstream",
            opening_topic="gate/gate_1/opening",
            state_topic="gate/gate_1/state"
        )
        # Call setup on all agents to register subscriptions
        inflow_agent.setup()
        tank_agent.setup()
        pid_agent.setup()
        gate_agent.setup()

        # The gate's calculated flow will act as the tank's release outflow
        bus.subscribe(gate_agent, "tank/tank_1/state") # for upstream_level

        # Manually connect gate outflow to tank outflow
        # In a real system, a dedicated agent or a configuration would handle this.
        class GateToTankConnector:
            def on_message(self, message: Message):
                if message.topic == "gate/gate_1/state":
                    flow = message.payload.get("flow", 0)
                    tank_agent.model.input.release_outflow = flow

        bus.subscribe(GateToTankConnector(), "gate/gate_1/state")


        # 2. Simulation Loop
        initial_tank_level = tank_agent.model.state.level
        print(f"Initial Tank Level: {initial_tank_level}")

        for t in range(10):
            print(f"\n--- Time Step {t} ---")

            # The order of execution and dispatch is critical in a manual loop.
            # 1. Inflow agent generates inflow for the tank.
            inflow_agent.execute(t)
            bus.dispatch() # Deliver the inflow message.

            # 2. PID agent calculates opening based on the *previous* step's tank level.
            pid_agent.execute(t)
            bus.dispatch() # Deliver the opening command to the gate.

            # 3. Gate agent calculates flow based on the opening command and *previous* tank level.
            gate_agent.execute(t)
            bus.dispatch() # Deliver the gate's flow state.

            # 4. Tank agent's outflow is updated by the connector, then it calculates its new level.
            tank_agent.execute(t)
            bus.dispatch() # Deliver the tank's new state for the next loop.

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
