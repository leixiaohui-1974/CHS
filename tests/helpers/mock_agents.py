import sys
import os

# Add the parent directory to the path to allow imports from chs_sdk
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from chs_sdk.agents.message import Message
from chs_sdk.agents.base import BaseAgent
from chs_sdk.core.host import AgentKernel

# --- Generic Mock Agent ---

class MockAgent(BaseAgent):
    """A generic mock agent for testing lifecycle and basic properties."""
    def __init__(self, agent_id: str, kernel: 'AgentKernel', **config):
        super().__init__(agent_id, kernel, **config)
        self.setup_called = False
        self.execute_count = 0
        self.shutdown_called = False
        self.received_messages = []

    def setup(self):
        self.setup_called = True

    def on_execute(self, current_time: float, time_step: float):
        self.execute_count += 1

    def on_message(self, message: Message):
        self.received_messages.append(message)

    def shutdown(self):
        self.shutdown_called = True

# --- Agents for Request-Response Testing (used in test_agent_framework) ---

class RequestResponsePingAgent(MockAgent):
    """A mock agent that sends a 'ping' on its first execution step to 'pong_topic'."""
    def on_execute(self, current_time: float, time_step: float):
        super().on_execute(current_time, time_step)
        if self.execute_count == 1:
            self._publish("pong_topic", {"content": "ping"})


class RequestResponsePongAgent(MockAgent):
    """A mock agent that listens on 'pong_topic' and responds to 'ping_topic'."""
    def setup(self):
        super().setup()
        self.kernel.message_bus.subscribe(self, "pong_topic")

    def on_message(self, message: Message):
        super().on_message(message)
        if message.topic == "pong_topic":
            self._publish("ping_topic", {"content": "pong"})

# --- Agents for One-Way Communication Testing (used in test_agent_communication) ---

class OneWayPingAgent(BaseAgent):
    """An agent that sends a single "ping" message to 'test/ping' and then does nothing."""
    def __init__(self, agent_id, kernel, **config):
        super().__init__(agent_id, kernel, **config)
        self.ping_sent = False

    def on_execute(self, current_time: float, time_step: float):
        if not self.ping_sent:
            self._publish("test/ping", "ping")
            self.ping_sent = True

    def setup(self):
        pass

    def on_message(self, message: Message):
        pass # Not expecting messages

    def shutdown(self):
        pass

# --- Utility Agents ---

class LoggerAgent(BaseAgent):
    """
    A utility agent that subscribes to a topic and records all message
    payloads it receives into a history list.
    """
    def __init__(self, agent_id: str, kernel: 'AgentKernel', **config):
        super().__init__(agent_id, kernel, **config)
        self.topic_to_subscribe = config.get("topic_to_subscribe", "default/topic")
        self.history = []

    def setup(self):
        super().setup()
        self.kernel.message_bus.subscribe(self, self.topic_to_subscribe)

    def on_execute(self, current_time: float, time_step: float):
        pass # Purely reactive

    def on_message(self, message: Message):
        self.history.append(message.payload)

    def shutdown(self):
        pass


class OneWayPongAgent(BaseAgent):
    """An agent that listens on 'test/ping' and records the last message it received."""
    def __init__(self, agent_id, kernel, **config):
        super().__init__(agent_id, kernel, **config)
        self.last_message: Message | None = None

    def setup(self):
        super().setup()
        self.kernel.message_bus.subscribe(self, "test/ping")

    def on_execute(self, current_time: float, time_step: float):
        pass # Logic is reactive in on_message

    def on_message(self, message: Message):
        self.last_message = message

    def shutdown(self):
        pass
