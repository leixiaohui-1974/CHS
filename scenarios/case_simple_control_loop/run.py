import sys
import os
import yaml

# Add the project root and the src directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
src_path = os.path.join(project_root, 'water_system_sdk', 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

from chs_sdk.core.launcher import Launcher

def main():
    """
    Main function to load the config and run the scenario.
    """
    # Construct the absolute path to the config file
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')

    try:
        with open(config_path, 'r') as f:
            scenario_config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found at '{config_path}'")
        return
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        return

    # Instantiate and run the launcher
    launcher = Launcher()
    launcher.run(scenario_config)

if __name__ == "__main__":
    main()
