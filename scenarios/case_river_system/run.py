import os
import sys

# Add the project root to the Python path to allow for absolute imports
# This is necessary because the launcher is run from within the scenarios directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from scenarios.launcher import main as launcher_main

if __name__ == "__main__":
    # Set the config file argument for the launcher
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    sys.argv = [sys.argv[0], '--config', config_path]

    print(f"--- Running River System Integration Test ---")
    print(f"Using config file: {config_path}")

    launcher_main()

    print(f"--- River System Integration Test Finished ---")
