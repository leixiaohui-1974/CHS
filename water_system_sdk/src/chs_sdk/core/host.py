import time
from typing import Dict, List, Type

from ..utils.logger import log
from ..agents.agent_status import AgentStatus
from ..agents.base import BaseAgent
from ..agents.message_bus import BaseMessageBus, InMemoryMessageBus


class AgentKernel:
    """
    The AgentKernel is the core of the agent-based simulation framework.
    It manages the lifecycle of all agents, handles errors gracefully,
    and provides observability into agent performance.
    """

    def __init__(self, message_bus: BaseMessageBus = None):
        """
        Initializes the AgentKernel.
        - message_bus: An optional message bus instance. If not provided,
                       an InMemoryMessageBus will be created.
        """
        self.message_bus = message_bus if message_bus else InMemoryMessageBus()
        self._agents: Dict[str, BaseAgent] = {}
        self._agent_configs: Dict[str, dict] = {} # To store initial configs for restarts
        self._agent_types: Dict[str, Type[BaseAgent]] = {} # To store agent classes for restarts
        self._is_running = False
        self.current_time = 0.0
        self.time_step = 1.0
        self._performance_probes: Dict[str, float] = {} # To store execution times

        log.info("AgentKernel V2.0 Initialized.")

    def add_agent(self, agent_class: Type[BaseAgent], agent_id: str, **config):
        """
        Instantiates and adds an agent to the kernel.
        Stores the configuration for potential restarts.
        """
        if agent_id in self._agents:
            raise ValueError(f"Agent with id '{agent_id}' already exists.")

        log.info(f"Adding agent '{agent_id}' of type '{agent_class.__name__}'.")
        # Store config and type for potential restarts
        self._agent_configs[agent_id] = config
        self._agent_types[agent_id] = agent_class

        # Create instance and add it to the kernel
        agent_instance = agent_class(agent_id=agent_id, kernel=self, **config)
        self._agents[agent_id] = agent_instance
        self._performance_probes[agent_id] = 0.0


    def _setup_agents(self):
        """
        Calls the setup() method on all registered agents and sets their status to RUNNING.
        """
        log.info("Setting up all registered agents...")
        for agent in self._agents.values():
            try:
                agent.setup()
                agent.status = AgentStatus.RUNNING
                log.debug(f"Agent '{agent.agent_id}' setup complete and set to RUNNING.")
            except Exception as e:
                agent.status = AgentStatus.FAULT
                log.error(f"Error during setup of agent '{agent.agent_id}': {e}", exc_info=True)

    def _shutdown_agents(self):
        """
        Calls the shutdown() method on all registered agents.
        """
        log.info("Shutting down all agents...")
        for agent in self._agents.values():
            try:
                agent.status = AgentStatus.SHUTTING_DOWN
                agent.shutdown()
                log.debug(f"Agent '{agent.agent_id}' shutdown complete.")
            except Exception as e:
                log.error(f"Error during shutdown of agent '{agent.agent_id}': {e}", exc_info=True)


    def run(self, duration: float, time_step: float = 1.0):
        """
        Runs the simulation for a given duration with a specific time step.
        Includes error handling and performance monitoring for agent execution.
        """
        log.info(f"AgentKernel run starting. Duration: {duration}, Time Step: {time_step}")
        self._is_running = True
        self._setup_agents()

        self.time_step = time_step
        end_time = self.current_time + duration

        while self._is_running and self.current_time < end_time:
            start_of_tick = time.perf_counter()

            # 1. Execute agent logic for all running agents
            for agent in list(self._agents.values()):
                if agent.status == AgentStatus.RUNNING:
                    try:
                        start_time = time.perf_counter()
                        agent.execute(self.current_time, self.time_step)
                        end_time_agent = time.perf_counter()
                        self._performance_probes[agent.agent_id] = end_time_agent - start_time
                    except Exception as e:
                        agent.status = AgentStatus.FAULT
                        log.error(
                            f"Error executing agent '{agent.agent_id}'. Agent set to FAULT. Error: {e}",
                            exc_info=True
                        )

            # 2. Dispatch messages from the message bus
            self.message_bus.dispatch()

            # 3. Advance time
            self.current_time += time_step

            end_of_tick = time.perf_counter()
            log.trace(f"Tick {self.current_time:.2f} processed in {end_of_tick - start_of_tick:.4f} seconds.")


        self._shutdown_agents()
        self._is_running = False
        log.info("AgentKernel run finished.")

    def tick(self):
        """
        Executes a single time step of the simulation.
        This is a simplified version of the logic within run().
        """
        if not self._is_running:
            log.warning("tick() called but kernel is not running. Call start() first.")
            return

        # 1. Execute agent logic for all running agents
        for agent in list(self._agents.values()):
            if agent.status == AgentStatus.RUNNING:
                try:
                    start_time = time.perf_counter()
                    agent.execute(self.current_time, self.time_step)
                    end_time_agent = time.perf_counter()
                    self._performance_probes[agent.agent_id] = end_time_agent - start_time
                except Exception as e:
                    agent.status = AgentStatus.FAULT
                    log.error(
                        f"Error executing agent '{agent.agent_id}'. Agent set to FAULT. Error: {e}",
                        exc_info=True
                    )

        # 2. Dispatch messages from the message bus
        self.message_bus.dispatch()

        # 3. Advance time
        self.current_time += self.time_step

    def start(self, time_step: float = 1.0):
        """
        Prepares the kernel for a tick-based run.
        """
        log.info(f"AgentKernel starting for tick-based execution.")
        self.time_step = time_step
        if not self._is_running:
            self._is_running = True
            self._setup_agents()

    def stop(self):
        """
        Stops the simulation loop gracefully and shuts down agents.
        """
        if self._is_running:
            log.info("Stop signal received. Shutting down kernel.")
            self._shutdown_agents()
            self._is_running = False

    def get_agent_performance(self) -> Dict[str, float]:
        """
        Returns the last recorded execution time for each agent.
        """
        return self._performance_probes.copy()

    def restart_agent(self, agent_id: str) -> bool:
        """
        Restarts a faulty agent.
        This involves removing the old instance and creating a new one with the original configuration.
        """
        if agent_id not in self._agents or self._agents[agent_id].status != AgentStatus.FAULT:
            log.warning(f"Restart requested for non-faulty or non-existent agent '{agent_id}'.")
            return False

        log.info(f"Restarting agent '{agent_id}'...")

        # Get original config and class
        agent_class = self._agent_types.get(agent_id)
        config = self._agent_configs.get(agent_id)

        if not agent_class or config is None:
            log.error(f"Cannot restart agent '{agent_id}': original class or config not found.")
            return False

        # Create and set up the new instance
        try:
            new_agent_instance = agent_class(agent_id=agent_id, kernel=self, **config)
            self._agents[agent_id] = new_agent_instance # Replace the old instance
            new_agent_instance.setup()
            new_agent_instance.status = AgentStatus.RUNNING
            log.info(f"Agent '{agent_id}' restarted successfully and is now RUNNING.")
            return True
        except Exception as e:
            log.error(f"Failed to restart agent '{agent_id}': {e}", exc_info=True)
            # Ensure the faulty agent is not left in a weird state
            if agent_id in self._agents:
                self._agents[agent_id].status = AgentStatus.FAULT
            return False
