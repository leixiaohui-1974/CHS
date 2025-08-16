import pytest
from chs_sdk.core.host import AgentKernel
from chs_sdk.agents.base import BaseAgent
from chs_sdk.agents.message import Message

class PingAgent(BaseAgent):
    """
    An agent that sends a single "ping" message and then does nothing.
    """
    def __init__(self, agent_id, kernel, **config):
        super().__init__(agent_id, kernel, **config)
        self.ping_sent = False

    def execute(self, current_time: float):
        if not self.ping_sent:
            print(f"[{self.agent_id}] Sending ping at time {current_time}")
            self._publish("test/ping", "ping")
            self.ping_sent = True

    def on_message(self, message: Message):
        pass # Not expecting messages

class PongAgent(BaseAgent):
    """
    An agent that listens for "ping" messages and records the last one it received.
    """
    def __init__(self, agent_id, kernel, **config):
        super().__init__(agent_id, kernel, **config)
        self.last_message: Message | None = None

    def setup(self):
        super().setup()
        print(f"[{self.agent_id}] Subscribing to topic 'test/ping'")
        self.kernel.message_bus.subscribe(self, "test/ping")

    def execute(self, current_time: float):
        pass # Logic is reactive in on_message

    def on_message(self, message: Message):
        print(f"[{self.agent_id}] Received message: {message.payload}")
        self.last_message = message

def test_ping_pong_communication():
    """
    Verifies that two agents can communicate via the InMemoryMessageBus.
    """
    # 1. Initialize Kernel
    kernel = AgentKernel()

    # 2. Create and add agents
    kernel.add_agent(PingAgent, agent_id="ping_agent_1")
    kernel.add_agent(PongAgent, agent_id="pong_agent_1")
    pong_agent = kernel._agents["pong_agent_1"]

    # 3. Run the simulation for a few steps
    # Duration of 2.0 with time_step 1.0 means 2 execute() calls.
    # The first call sends the ping. The message is dispatched.
    # The second call ensures the pong agent is still running, though it does nothing.
    kernel.run(duration=2.0, time_step=1.0)

    # 4. Assert results
    assert pong_agent.last_message is not None, "PongAgent did not receive any message"
    assert pong_agent.last_message.sender_id == "ping_agent_1"
    assert pong_agent.last_message.topic == "test/ping"
    assert pong_agent.last_message.payload == "ping"
