# scenarios/case_centralized_mpc/run.py
import sys
import os
import yaml
import argparse

# Add the project root to the Python path to allow for absolute imports
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC_DIR = os.path.join(ROOT_DIR, 'water_system_sdk', 'src')
sys.path.insert(0, SRC_DIR)
sys.path.insert(0, ROOT_DIR)


from scenarios.launcher import Launcher

def main():
    # Set the config file argument for the launcher
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')

    parser = argparse.ArgumentParser(description="Run Centralized MPC Scenario")
    parser.add_argument('--config', type=str, default=config_path, help='Path to the scenario config file')
    args = parser.parse_args()

    print(f"--- Running Centralized MPC System Integration Test ---")
    print(f"Using configuration file: {args.config}")

    with open(args.config, 'r') as f:
        scenario_config = yaml.safe_load(f)

    launcher = Launcher()
    launcher.run(scenario_config)

    print("--- Centralized MPC System Integration Test Finished ---")

if __name__ == "__main__":
    main()
