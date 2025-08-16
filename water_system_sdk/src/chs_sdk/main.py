from __future__ import annotations
import os
import json
import copy
import logging
import time
from enum import Enum
from typing import List, Dict, Any, TYPE_CHECKING

from .agents.agent_status import AgentStatus

# Local application imports
if TYPE_CHECKING:
    from .agents.base import BaseAgent
    from .agents.message_bus import InMemoryMessageBus as MessageBus

# It's good practice to have a logger instance per module.
logger = logging.getLogger(__name__)

# --- New Agent-Based Simulation Kernel ---

class SimulationMode(Enum):
    """
    Defines the operational modes for the simulation engine, as per the design document.
    """
    SIL = "Software-in-the-Loop"  # Pure software simulation
    HIL = "Hardware-in-the-Loop"  # Connects to real hardware
    HITL = "Human-in-the-Loop"    # Includes human operators

class SimulationEngine:
    """
    The core of the CHS-SDK, a multi-mode mother machine platform.
    It orchestrates the simulation by managing agents, the message bus,
    and the main time loop.
    """
    def __init__(self, mode: SimulationMode, agents: List[BaseAgent], message_bus: MessageBus):
        self.mode = mode
        self.agents = agents
        self.message_bus = message_bus
        self.is_running = False
        self.current_time_seconds = 0.0

        logger.info(f"SimulationEngine initialized in {self.mode.name} mode with {len(self.agents)} agents.")

        # Register all agents with the message bus
        for agent in self.agents:
            # This anticipates the refactoring in Step 4 where agents will have a message_bus property
            # and a standardized 'agent_id' attribute.
            if hasattr(agent, 'agent_id'):
                self.message_bus.subscribe(agent, "#") # Subscribe to all topics for now
            else:
                logger.warning(f"Agent of type {type(agent).__name__} does not have an 'agent_id' attribute and cannot be registered.")


    def run(self, duration_seconds: float, time_step_seconds: float):
        """
        Executes the main simulation loop.

        Args:
            duration_seconds: The total duration of the simulation in seconds.
            time_step_seconds: The time increment for each simulation step.
        """
        logger.info(f"Starting simulation run. Duration: {duration_seconds}s, Time Step: {time_step_seconds}s.")
        self.time_step = time_step_seconds # Store time_step for agents to access

        # Set all agents to RUNNING state before starting the loop
        for agent in self.agents:
            agent.status = AgentStatus.RUNNING

        self.is_running = True
        stop_time = self.current_time_seconds + duration_seconds

        while self.is_running and self.current_time_seconds < stop_time:
            logger.debug(f"Simulation step at t = {self.current_time_seconds:.2f}s")

            # 1. Dispatch messages from the previous step to update agent states
            self.message_bus.dispatch()

            # 2. Execute agents, who will use the new state and publish new messages
            for agent in self.agents:
                try:
                    agent.execute(self.current_time_seconds, time_step_seconds)
                except Exception as e:
                    agent_id = getattr(agent, 'agent_id', 'N/A')
                    logger.error(f"Error in execute() of agent '{agent_id}': {e}", exc_info=True)

            # 3. Dispatch messages published in the current step, so they are processed before the next execute
            self.message_bus.dispatch()

            # 4. Advance simulation time
            self.current_time_seconds += time_step_seconds

            # In a real-time simulation (HIL/HITL), we would sleep to match wall-clock time.
            # For pure SIL, we can run as fast as possible.
            if self.mode in [SimulationMode.HIL, SimulationMode.HITL]:
                time.sleep(time_step_seconds)

        logger.info("Simulation run finished.")
        self.is_running = False

    def stop(self):
        """Stops the simulation loop gracefully."""
        logger.info("Stopping simulation engine.")
        self.is_running = False

def main():
    """
    New main function demonstrating the SimulationEngine.
    """
    # from .agents.communication import MessageBus # Commented out due to refactoring
    # from .agents.base import BaseAgent # Commented out due to refactoring

    # --- Basic logging setup ---
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # A simple dummy agent for demonstration purposes
    class TickerAgent(BaseAgent):
        def __init__(self, id: str, message_bus: MessageBus, **kwargs):
            # BaseAgent now handles id and message_bus assignment.
            super().__init__(id=id, message_bus=message_bus, **kwargs)

        def step(self, dt: float, **kwargs):
            logging.info(f"Agent '{self.id}' tick. Current sim time: {kwargs.get('current_time', 'N/A'):.2f}s")
            # Example of using the message bus from the agent instance
            if self.message_bus:
                self.message_bus.publish(f"agent.{self.id}.heartbeat", {"timestamp": time.time()}, sender_id=self.id)

        def get_state(self) -> Dict[str, Any]:
            return {"id": self.id, "status": "ticking"}

    # 1. Initialize the MessageBus
    message_bus = MessageBus()

    # 2. Create agents, now passing the message bus to them
    agent1 = TickerAgent(id="agent_alpha", message_bus=message_bus)
    agent2 = TickerAgent(id="agent_beta", message_bus=message_bus)

    # 3. Initialize the SimulationEngine
    engine = SimulationEngine(
        mode=SimulationMode.SIL,
        agents=[agent1, agent2],
        message_bus=message_bus
    )

    # 4. Run the simulation
    engine.run(duration_seconds=5.0, time_step_seconds=1.0)


if __name__ == "__main__":
    # The new main function is now the entry point.
    main()
