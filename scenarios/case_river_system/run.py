import os
import sys

# Adjust the Python path to include the source directory of the SDK
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC_DIR = os.path.join(ROOT_DIR, 'water_system_sdk', 'src')
sys.path.insert(0, SRC_DIR)
sys.path.insert(0, ROOT_DIR)


from scenarios.launcher import main as launcher_main

if __name__ == "__main__":
    # Set the config file argument for the launcher
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    sys.argv = [sys.argv[0], '--config', config_path]

    print(f"--- Running River System Integration Test ---")
    print(f"Using config file: {config_path}")

    launcher_main()

    print(f"--- River System Integration Test Finished ---")
