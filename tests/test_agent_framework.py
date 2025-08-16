import unittest
import time
import sys
import os

# Add the parent directory to the path to allow imports from chs_sdk
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from chs_sdk.agents.message import Message
from chs_sdk.agents.base import BaseAgent
from chs_sdk.core.host import AgentKernel
from chs_sdk.agents.message_bus import InMemoryMessageBus

# --- Mock Agents for Testing ---

class MockAgent(BaseAgent):
    def __init__(self, agent_id: str, kernel: 'AgentKernel', **config):
        super().__init__(agent_id, kernel, **config)
        self.setup_called = False
        self.execute_count = 0
        self.shutdown_called = False
        self.received_messages = []

    def setup(self):
        self.setup_called = True

    def execute(self, current_time: float):
        self.execute_count += 1

    def on_message(self, message: Message):
        self.received_messages.append(message)

    def shutdown(self):
        self.shutdown_called = True


class PingAgent(MockAgent):
    def execute(self, current_time: float):
        super().execute(current_time)
        # On the first step, publish a ping message
        if self.execute_count == 1:
            self._publish("pong_topic", {"content": "ping"})


class PongAgent(MockAgent):
    def setup(self):
        super().setup()
        self.kernel.message_bus.subscribe(self, "pong_topic")

    def on_message(self, message: Message):
        super().on_message(message)
        if message.topic == "pong_topic":
            self._publish("ping_topic", {"content": "pong"})


# --- Test Cases ---

class TestAgentFramework(unittest.TestCase):

    def test_message_creation(self):
        """
        Tests the creation of a Message object.
        """
        msg = Message(topic="test", sender_id="agent1", payload={"data": 123})
        self.assertEqual(msg.topic, "test")
        self.assertEqual(msg.sender_id, "agent1")
        self.assertIsInstance(msg.timestamp, float)
        self.assertEqual(msg.payload, {"data": 123})

    def test_agent_lifecycle(self):
        """
        Tests that the kernel correctly manages the agent lifecycle.
        """
        kernel = AgentKernel()
        kernel.add_agent(MockAgent, agent_id="mock1")
        agent = kernel._agents["mock1"]

        self.assertFalse(agent.setup_called)
        self.assertEqual(agent.execute_count, 0)
        self.assertFalse(agent.shutdown_called)

        kernel.run(duration=3, time_step=1) # Should run for 3 steps (0, 1, 2)

        self.assertTrue(agent.setup_called)
        self.assertEqual(agent.execute_count, 3)
        self.assertTrue(agent.shutdown_called)

    def test_message_passing(self):
        """
        Tests the full message passing loop between two agents.
        """
        kernel = AgentKernel()

        # Create and add agents
        kernel.add_agent(PingAgent, agent_id="pinger")
        kernel.add_agent(PongAgent, agent_id="ponger")
        pinger = kernel._agents["pinger"]
        ponger = kernel._agents["ponger"]

        # Pinger subscribes to the return topic
        kernel.message_bus.subscribe(pinger, "ping_topic")

        # Run the simulation
        kernel.run(duration=2, time_step=1) # 2 steps

        # --- Assertions ---
        # Pinger should have sent one message
        # Ponger should have received one message and sent one back
        # Pinger should have received the pong back

        self.assertEqual(len(ponger.received_messages), 1)
        pong_message = ponger.received_messages[0]
        self.assertEqual(pong_message.topic, "pong_topic")
        self.assertEqual(pong_message.sender_id, "pinger")
        self.assertEqual(pong_message.payload, {"content": "ping"})

        self.assertEqual(len(pinger.received_messages), 1)
        ping_message = pinger.received_messages[0]
        self.assertEqual(ping_message.topic, "ping_topic")
        self.assertEqual(ping_message.sender_id, "ponger")
        self.assertEqual(ping_message.payload, {"content": "pong"})

        # Check execution counts
        self.assertEqual(pinger.execute_count, 2)
        self.assertEqual(ponger.execute_count, 2)

    def test_add_duplicate_agent_id_raises_error(self):
        """
        Tests that adding an agent with a duplicate ID raises a ValueError.
        """
        kernel = AgentKernel()
        kernel.add_agent(MockAgent, agent_id="agent1")
        with self.assertRaises(ValueError):
            kernel.add_agent(MockAgent, agent_id="agent1")

if __name__ == '__main__':
    unittest.main()
