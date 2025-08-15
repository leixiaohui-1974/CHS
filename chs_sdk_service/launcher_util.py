import importlib
from typing import Dict, Any, List

from chs_sdk.agents.agent_kernel import AgentKernel
from chs_sdk.agents.message_bus import InMemoryMessageBus
from chs_sdk.agents.management_agents import DataCaptureAgent

from .models import ScenarioConfig


def run_simulation_and_capture_data(scenario_config: ScenarioConfig) -> List[Dict[str, Any]]:
    """
    Runs a simulation based on a scenario config and returns the captured data.

    This function dynamically injects a DataCaptureAgent into the agent society
    to collect all messages during the simulation run.

    Args:
        scenario_config: The Pydantic model representing the simulation scenario.

    Returns:
        A list of dictionaries, where each dictionary is a captured message.
    """
    # Define a unique ID for our capture agent
    capture_agent_id = "api_data_capture_agent_001"

    # Convert Pydantic model to a dictionary for manipulation
    config_dict = scenario_config.dict(by_alias=True)

    # Add the DataCaptureAgent to the agent society
    # It will capture all messages by default ("#")
    config_dict["agent_society"].append({
        "id": capture_agent_id,
        "class": "chs_sdk.agents.management_agents.DataCaptureAgent",
        "params": {"topics_to_log": ["#"]}
    })

    # 1. Initialize the kernel and message bus
    message_bus = InMemoryMessageBus()
    kernel = AgentKernel(message_bus=message_bus)

    agent_instances = {}

    # 2. Instantiate and add agents to the kernel
    for agent_config in config_dict["agent_society"]:
        try:
            class_path = agent_config["class"]
            module_path, class_name = class_path.rsplit('.', 1)

            module = importlib.import_module(module_path)
            agent_class = getattr(module, class_name)

            params = agent_config.get("params", {})
            agent_id = agent_config["id"]

            # The kernel is now responsible for instantiation
            kernel.add_agent(agent_class, agent_id, **params)

        except (ImportError, AttributeError, KeyError, TypeError) as e:
            # Consider raising a custom exception here to be caught by the API endpoint
            raise RuntimeError(f"Error loading agent '{agent_config.get('id', 'N/A')}': {e}") from e

    # 3. Get simulation settings and run the kernel
    sim_settings = config_dict.get("simulation_settings", {})
    duration = sim_settings.get("duration", 100)
    time_step = sim_settings.get("time_step", 1.0)

    kernel.run(duration=duration, time_step=time_step)

    # 4. Retrieve the capture agent and return its data
    # The `add_agent` method in the kernel creates the instance, we need to get it back.
    # The kernel stores agent instances in a dictionary called `_agents`.
    # This is an internal detail, but necessary for this implementation.
    capture_agent_instance = kernel._agents.get(capture_agent_id)

    if capture_agent_instance and isinstance(capture_agent_instance, DataCaptureAgent):
        return capture_agent_instance.get_data()

    return []
