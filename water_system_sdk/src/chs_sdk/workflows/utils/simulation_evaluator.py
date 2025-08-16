import numpy as np
from typing import Dict, Any
import importlib

# The Launcher is a core component for running simulations
from chs_sdk.core.host import AgentKernel
from chs_sdk.agents.message_bus import InMemoryMessageBus
from chs_sdk.core.launcher import Launcher
from chs_sdk.agents.management_agents import DataCaptureAgent
from chs_sdk.agents.control_agents import PIDAgent
from chs_sdk.agents.disturbance_agents import InflowAgent

def evaluate_control_performance(
    system_model: Dict[str, Any],
    controller_config: Dict[str, Any],
    objective: str,
    duration: int = 100,
    time_step: float = 1.0
) -> float:
    """
    Runs a simulation to evaluate the performance of a controller on a system.
    This version is generalized to handle any body agent passed via system_model.
    """
    capture_agent_id = "data_capture_1"

    # --- Dynamic Scenario Construction ---
    sut_id = system_model.get("id", "system_under_test")
    pid_id = "pid_1"
    inflow_id = "inflow_1"

    # Generic topics based on the System Under Test (SUT)
    sut_state_topic = f"state/{sut_id}"
    sut_control_input_topic = f"control/{sut_id}/inflow" # Topic the PID controls
    sut_control_output_topic = f"control/{sut_id}/outflow" # Topic the PID measures (not used by PID directly)

    # Disturbance inflow will be sent to the SUT's control input topic
    step_time = duration // 2
    inflow_pattern = [10.0] * step_time + [15.0] * (duration - step_time)
    set_point = 10.0 # Target for the state variable

    # Dynamically create the system agent config from the passed model
    system_agent_config = {
        "id": sut_id,
        "class": system_model["class"],
        # Pass all necessary topics to the agent's params
        "params": {
            **system_model.get("params", {}),
            "inflow_topic": sut_control_input_topic,
            "state_topic": sut_state_topic,
        },
    }

    scenario_config = {
        "simulation_settings": {"duration": duration, "time_step": time_step},
        "agent_society": [
            {
                "id": inflow_id,
                "class": "chs_sdk.agents.disturbance_agents.InflowAgent",
                "params": {"topic": sut_control_input_topic, "rainfall_pattern": inflow_pattern},
            },
            system_agent_config, # Use the dynamically created config
            {
                "id": pid_id,
                "class": "chs_sdk.agents.control_agents.PIDAgent",
                "params": {
                    **controller_config,
                    "set_point": set_point,
                    "input_topic": sut_state_topic,
                    "output_topic": sut_control_input_topic, # PID output drives the SUT's input
                },
            },
            {
                "id": capture_agent_id,
                "class": "chs_sdk.agents.management_agents.DataCaptureAgent",
                "params": {"topics_to_log": [sut_state_topic]},
            }
        ],
    }

    # --- Run Simulation ---
    message_bus = InMemoryMessageBus()
    kernel = AgentKernel(message_bus=message_bus)
    agent_instances = {}

    for agent_config in scenario_config["agent_society"]:
        class_path = agent_config["class"]
        module_path, class_name = class_path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        agent_class = getattr(module, class_name)
        agent_id = agent_config["id"]
        instance = agent_class(agent_id=agent_id, kernel=kernel, **agent_config.get("params", {}))
        kernel._agents[agent_id] = instance
        agent_instances[agent_id] = instance

    kernel.run(duration=duration, time_step=time_step)

    # --- Calculate Performance Metric ---
    capture_agent_instance = agent_instances[capture_agent_id]
    data = capture_agent_instance.get_data()

    if not data:
        return float('inf')

    # The state variable to track might not be 'level' anymore.
    # We need to generalize this. Let's assume the state payload is a dict
    # and we track the first value in it. This is a heuristic.
    try:
        # Get the key of the state variable (e.g., 'outflow', 'level')
        first_payload = data[0]['payload']
        state_key = next(iter(first_payload))

        values = np.array([d['payload'][state_key] for d in data])
        times = np.array([d['time'] for d in data])
        errors = set_point - values
    except (IndexError, KeyError, StopIteration):
         return float('inf') # Failed to extract data

    cost = 0.0
    if objective.upper() == 'ISE':
        cost = np.sum(errors**2) * time_step
    elif objective.upper() == 'IAE':
        cost = np.sum(np.abs(errors)) * time_step
    # Add other objectives as needed
    else:
        raise ValueError(f"Unknown objective function: '{objective}'")

    return cost
