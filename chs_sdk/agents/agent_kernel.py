import time
from typing import List, Dict

from .base_agent import BaseAgent
from .message_bus import BaseMessageBus, InMemoryMessageBus


class AgentKernel:
    """
    The AgentKernel is the core of the agent-based simulation framework.
    It manages the lifecycle of all agents and drives the simulation forward.
    """

    def __init__(self, message_bus: BaseMessageBus = None):
        """
        Initializes the AgentKernel.
        - message_bus: An optional message bus instance. If not provided,
                       an InMemoryMessageBus will be created.
        """
        self.message_bus = message_bus if message_bus else InMemoryMessageBus()
        self._agents: Dict[str, BaseAgent] = {}
        self._is_running = False
        self.current_time = 0.0
        self.time_step = 1.0 # Default time step

    def add_agent(self, agent: BaseAgent):
        """
        Adds an agent to the kernel.
        """
        if agent.agent_id in self._agents:
            raise ValueError(f"Agent with id '{agent.agent_id}' already exists.")
        self._agents[agent.agent_id] = agent
        # The agent's __init__ should have set the kernel, but we can be sure here.
        agent.kernel = self

    def _setup_agents(self):
        """
        Calls the setup() method on all registered agents.
        """
        for agent in self._agents.values():
            agent.setup()

    def _shutdown_agents(self):
        """
        Calls the shutdown() method on all registered agents.
        """
        for agent in self._agents.values():
            agent.shutdown()

    def run(self, duration: float, time_step: float = 1.0):
        """
        Runs the simulation for a given duration with a specific time step.

        - duration: The total time to run the simulation for (in seconds).
        - time_step: The time increment for each simulation step (in seconds).
        """
        self._is_running = True
        self._setup_agents()

        self.time_step = time_step
        end_time = self.current_time + duration

        while self._is_running and self.current_time < end_time:
            # 1. Execute agent logic
            for agent in self._agents.values():
                agent.execute(self.current_time)

            # 2. Dispatch messages from the message bus
            self.message_bus.dispatch()

            # 3. Advance time
            self.current_time += time_step

        self._shutdown_agents()
        self._is_running = False

    def stop(self):
        """
        Stops the simulation loop.
        """
        self._is_running = False
