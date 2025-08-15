import numpy as np
from typing import Dict, Any

# Assuming the launcher and agents are accessible via these paths
# This might need adjustment based on the final project structure
from scenarios.launcher import Launcher
from chs_sdk.agents.management_agents import DataCaptureAgent
from chs_sdk.agents.body_agents import TankAgent
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

    Args:
        system_model: A dictionary defining the system to be controlled.
                      Example: {'class': 'TankAgent', 'params': {'area': 100.0}}
        controller_config: A dictionary defining the controller parameters.
                           Example: {'Kp': 0.5, 'Ki': 0.1, 'Kd': 0.01}
        objective: The performance metric to calculate (e.g., 'ISE', 'IAE').
        duration: The total simulation time in seconds.
        time_step: The simulation time step in seconds.

    Returns:
        The calculated performance cost (a float).
    """
    # 1. Create a data capture agent instance to retrieve results
    # This instance must be passed to the kernel and then used to get data.
    # The Launcher creates its own kernel, so we need a way to access the agent
    # instance after the run. We will instantiate it here and pass it into the config.
    capture_agent_id = "data_capture_1"
    capture_agent = DataCaptureAgent(agent_id=capture_agent_id, kernel=None) # Kernel is set by Launcher

    # --- Dynamic Scenario Construction ---
    # Define agent IDs for clarity
    tank_id = "tank_1"
    pid_id = "pid_1"
    inflow_id = "inflow_1"

    # Define topics based on agent IDs
    tank_state_topic = f"tank/{tank_id}/state"
    tank_inflow_topic = f"tank/{tank_id}/inflow"
    tank_outflow_topic = f"tank/{tank_id}/release_outflow"

    # Create a step-like disturbance using the InflowAgent
    step_time = duration // 2
    inflow_pattern = [10.0] * step_time + [15.0] * (duration - step_time)

    # The setpoint for the PID controller
    set_point = 10.0

    scenario_config = {
        "simulation_settings": {
            "duration": duration,
            "time_step": time_step,
        },
        "agent_society": [
            # a. Disturbance Agent (creates a step change in inflow)
            {
                "id": inflow_id,
                "class": "chs_sdk.agents.disturbance_agents.InflowAgent",
                "params": {
                    "topic": tank_inflow_topic,
                    "rainfall_pattern": inflow_pattern,
                },
            },
            # b. System Agent (the plant)
            {
                "id": tank_id,
                "class": "chs_sdk.agents.body_agents.TankAgent",
                "params": system_model.get('params', {}),
            },
            # c. Controller Agent
            {
                "id": pid_id,
                "class": "chs_sdk.agents.control_agents.PIDAgent",
                "params": {
                    "Kp": controller_config['Kp'],
                    "Ki": controller_config['Ki'],
                    "Kd": controller_config['Kd'],
                    "set_point": set_point,
                    "input_topic": tank_state_topic,
                    "output_topic": tank_outflow_topic,
                },
            },
            # d. Data Capture Agent
            # We need a way to get the instance back from the launcher, this config is tricky.
            # For now, let's assume the launcher can be modified or we can retrieve agents by id.
            # A cleaner way is to pass the instance directly, which requires a Launcher refactor.
            # Let's try a different approach for now and retrieve the agent from the kernel after run.
            {
                "id": capture_agent_id,
                "class": "chs_sdk.agents.management_agents.DataCaptureAgent",
                "params": {
                    "topics_to_log": [tank_state_topic]
                },
            }
        ],
    }

    # --- Run Simulation ---
    # The Launcher needs to be adapted to allow retrieving agents post-run
    # For now, let's assume a simplified Launcher for direct use
    from chs_sdk.agents.agent_kernel import AgentKernel
    from chs_sdk.agents.message_bus import InMemoryMessageBus
    import importlib

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
        kernel._agents[agent_id] = instance # Use internal access for now
        agent_instances[agent_id] = instance


    kernel.run(duration=duration, time_step=time_step)

    # --- Calculate Performance Metric ---
    capture_agent_instance = agent_instances[capture_agent_id]
    data = capture_agent_instance.get_data()

    if not data:
        # Return a large cost if no data was captured, indicating a failure
        return float('inf')

    # Extract relevant data
    times = np.array([d['time'] for d in data])
    levels = np.array([d['payload']['level'] for d in data])
    errors = set_point - levels

    cost = 0.0
    if objective.upper() == 'ISE':
        # Integral of Squared Error
        cost = np.sum(errors**2) * time_step
    elif objective.upper() == 'IAE':
        # Integral of Absolute Error
        cost = np.sum(np.abs(errors)) * time_step
    elif objective.upper() == 'ITSE':
        # Integral of Time-weighted Squared Error
        cost = np.sum(times * errors**2) * time_step
    elif objective.upper() == 'ITAE':
        # Integral of Time-weighted Absolute Error
        cost = np.sum(times * np.abs(errors)) * time_step
    else:
        raise ValueError(f"Unknown objective function: '{objective}'")

    return cost
