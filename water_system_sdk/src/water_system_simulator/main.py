from __future__ import annotations
import os
import json
import copy
import logging
import time
from enum import Enum
from typing import List, Dict, Any, TYPE_CHECKING

# Local application imports
if TYPE_CHECKING:
    from .agent.base_agent import BaseAgent
    from .agent.communication import MessageBus

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
            # and a standardized 'id' attribute.
            if hasattr(agent, 'id'):
                self.message_bus.register_agent(agent)
            else:
                logger.warning(f"Agent of type {type(agent).__name__} does not have an 'id' attribute and cannot be registered.")


    def run(self, duration_seconds: float, time_step_seconds: float):
        """
        Executes the main simulation loop.

        Args:
            duration_seconds: The total duration of the simulation in seconds.
            time_step_seconds: The time increment for each simulation step.
        """
        logger.info(f"Starting simulation run. Duration: {duration_seconds}s, Time Step: {time_step_seconds}s.")
        self.is_running = True

        stop_time = self.current_time_seconds + duration_seconds

        while self.is_running and self.current_time_seconds < stop_time:
            logger.debug(f"Simulation step at t = {self.current_time_seconds:.2f}s")

            # In each step, call the step() method of every agent
            for agent in self.agents:
                try:
                    # Pass the current time to the step method. The bus is now in the agent.
                    agent.step(time_step_seconds, current_time=self.current_time_seconds)
                except Exception as e:
                    agent_id = getattr(agent, 'id', 'N/A')
                    logger.error(f"Error in step() of agent '{agent_id}': {e}", exc_info=True)

            # Advance simulation time
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
    from .agent.communication import MessageBus
    from .agent.base_agent import BaseAgent

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

# --- Legacy Code ---
# The original functions from this file are preserved below for reference.
# They are not called by the new agent-based kernel.

def legacy_run_single_scenario(topology_data, base_params, timeseries_data, interception_enabled):
    """
    [LEGACY] Runs a single simulation scenario with a given parameter set.
    """
    from hydrology.core import Basin # Local import to avoid breaking if hydrology is removed
    scenario_params = copy.deepcopy(base_params)
    if "SubBasin1" in scenario_params:
        scenario_params["SubBasin1"]["human_activity_model"]["enabled"] = interception_enabled
    basin = Basin(
        topology_data=topology_data,
        params_data=scenario_params,
        timeseries_data=timeseries_data,
    )
    return basin.run_simulation(), basin.topology_data

def legacy_main():
    """
    [LEGACY] Main function to run and compare two scenarios.
    """
    from hydrology.utils.file_parsers import load_topology_from_json, load_timeseries_from_json
    import matplotlib.pyplot as plt

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    base_path = "data"
    topology_path = os.path.join(base_path, "topology.json")
    params_path = os.path.join(base_path, "parameters.json")
    timeseries_path = os.path.join(base_path, "timeseries.json")

    topology_data = load_topology_from_json(topology_path)
    timeseries_data = load_timeseries_from_json(timeseries_path)
    with open(params_path, 'r') as f:
        base_params = json.load(f)

    results_disabled, topology_data = legacy_run_single_scenario(
        topology_data, base_params, timeseries_data, interception_enabled=False
    )
    results_enabled, _ = legacy_run_single_scenario(
        topology_data, base_params, timeseries_data, interception_enabled=True
    )

    # ... (rest of legacy plotting code) ...

if __name__ == "__main__":
    # The new main function is now the entry point.
    main()
