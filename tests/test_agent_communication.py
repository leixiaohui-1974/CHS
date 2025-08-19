import pytest
from chs_sdk.core.host import AgentKernel
from chs_sdk.agents.message import Message
from tests.helpers.mock_agents import OneWayPingAgent, OneWayPongAgent


def test_ping_pong_communication():
    """
    Verifies that two agents can communicate via the InMemoryMessageBus.
    """
    # 1. Initialize Kernel
    kernel = AgentKernel()

    # 2. Create and add agents
    kernel.add_agent(OneWayPingAgent, agent_id="ping_agent_1")
    kernel.add_agent(OneWayPongAgent, agent_id="pong_agent_1")
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
