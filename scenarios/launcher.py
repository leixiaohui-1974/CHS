import yaml
import argparse
import importlib
from typing import Dict, Any

from chs_sdk.agents.agent_kernel import AgentKernel
from chs_sdk.agents.message_bus import InMemoryMessageBus

class Launcher:
    """
    The Launcher is responsible for setting up and running a simulation scenario
    based on a configuration file.
    """
    def __init__(self):
        pass

    def run(self, scenario_config: Dict[str, Any]):
        """
        Runs the simulation scenario.

        :param scenario_config: A dictionary containing the simulation settings
                                and agent society definition.
        """
        # 1. Initialize the kernel and message bus
        message_bus = InMemoryMessageBus()
        kernel = AgentKernel(message_bus=message_bus)

        # 2. Instantiate and add agents to the kernel
        agent_society_config = scenario_config.get("agent_society", [])
        for agent_config in agent_society_config:
            try:
                class_path = agent_config["class"]
                module_path, class_name = class_path.rsplit('.', 1)

                # Dynamically import the module and get the class
                module = importlib.import_module(module_path)
                agent_class = getattr(module, class_name)

                # Prepare agent parameters
                params = agent_config.get("params", {})
                agent_id = agent_config["id"]

                # Instantiate the agent
                # The kernel is now the primary way for agents to interact
                # with the system, including the message bus.
                params['agent_id'] = agent_id
                params['kernel'] = kernel

                agent_instance = agent_class(**params)

                # Add agent to the kernel
                kernel.add_agent(agent_instance)
                print(f"Successfully instantiated and added agent: {agent_id}")

            except (ImportError, AttributeError, KeyError, TypeError) as e:
                print(f"Error loading agent '{agent_config.get('id', 'N/A')}': {e}")
                # Depending on desired robustness, you might want to exit here
                return

        # 3. Get simulation settings and run the kernel
        sim_settings = scenario_config.get("simulation_settings", {})
        duration = sim_settings.get("duration", 100)
        time_step = sim_settings.get("time_step", 1.0)

        print(f"Starting simulation for {duration}s with a {time_step}s time step...")
        kernel.run(duration=duration, time_step=time_step)
        print("Simulation finished.")

def main():
    """
    Main function to parse arguments and run the launcher.
    """
    parser = argparse.ArgumentParser(description="CHS-SDK Scenario Launcher")
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to the scenario configuration YAML file."
    )
    args = parser.parse_args()

    try:
        with open(args.config, 'r') as f:
            scenario_config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found at '{args.config}'")
        return
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        return

    launcher = Launcher()
    launcher.run(scenario_config)

if __name__ == "__main__":
    main()
