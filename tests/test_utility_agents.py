import unittest
import sys
import os

# Add the parent directory to the path to allow imports from chs_sdk
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from chs_sdk.core.host import AgentKernel
from tests.helpers.mock_agents import LoggerAgent
from chs_sdk.agents.base import BaseAgent

class TestUtilityAgents(unittest.TestCase):

    def test_logger_agent(self):
        """
        Tests that the LoggerAgent correctly subscribes to a topic and
        records the history of message payloads.
        """
        # 1. Setup
        kernel = AgentKernel()
        log_topic = "test/log"

        # A simple agent to publish data for the logger to capture
        class DataSourceAgent(BaseAgent):
            def on_execute(self, current_time: float, time_step: float):
                self._publish(log_topic, {"time": current_time, "value": current_time * 10})

            def setup(self): pass
            def shutdown(self): pass
            def on_message(self, message): pass


        # 2. Add agents
        kernel.add_agent(
            LoggerAgent,
            agent_id="logger",
            topic_to_subscribe=log_topic
        )
        kernel.add_agent(DataSourceAgent, agent_id="source")

        logger = kernel._agents["logger"]

        # 3. Run simulation
        kernel.run(duration=3.0, time_step=1.0) # Will run at t=0, 1, 2

        # 4. Assertions
        self.assertEqual(len(logger.history), 3)
        self.assertEqual(logger.history[0], {"time": 0.0, "value": 0.0})
        self.assertEqual(logger.history[1], {"time": 1.0, "value": 10.0})
        self.assertEqual(logger.history[2], {"time": 2.0, "value": 20.0})
