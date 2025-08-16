import os
import yaml
from chs_sdk.core.launcher import Launcher

def main():
    """
    Loads and runs the V2 control loop scenario.
    """
    # Get the absolute path to the config file
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

    # Instantiate and run the launcher with the loaded configuration
    launcher = Launcher()
    launcher.run(scenario_config)

if __name__ == "__main__":
    main()
