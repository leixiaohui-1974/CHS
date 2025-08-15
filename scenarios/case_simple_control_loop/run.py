import sys
import os
import yaml

# Add the project root to the Python path to allow for absolute imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Also add the src directory for the SDK
src_path = os.path.join(project_root, 'water_system_sdk', 'src')
sys.path.insert(0, src_path)

from scenarios.launcher import Launcher

def main():
    """
    Main function to load config and run the launcher for the simple control loop case.
    """
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the path to the config file
    config_path = os.path.join(script_dir, 'config.yaml')

    try:
        with open(config_path, 'r') as f:
            scenario_config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found at '{config_path}'")
        return
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        return

    # Change the current working directory to the project root
    # to ensure that relative paths for logs/results are correct.
    os.chdir(project_root)

    launcher = Launcher()
    launcher.run(scenario_config)

if __name__ == "__main__":
    main()
