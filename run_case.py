import argparse
import yaml
import pandas as pd
import os
from chs_sdk.simulation_manager import SimulationManager

def main():
    """
    A generic command-line runner for CHS simulation cases.
    """
    parser = argparse.ArgumentParser(description="Run a CHS simulation case from a YAML file.")
    parser.add_argument(
        "yaml_path",
        type=str,
        help="Path to the simulation topology YAML file."
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="DYNAMIC",
        choices=["STEADY", "DYNAMIC", "PRECISION"],
        help="The simulation fidelity mode to run."
    )
    args = parser.parse_args()

    print(f"--- Loading simulation from: {args.yaml_path} ---")
    try:
        with open(args.yaml_path, 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found at '{args.yaml_path}'")
        return
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        return

    # --- Check for and merge control parameters ---
    case_dir = os.path.dirname(args.yaml_path)
    control_params_path = os.path.join(case_dir, 'control_parameters.yaml')
    if os.path.exists(control_params_path):
        print(f"--- Loading control parameters from: {control_params_path} ---")
        with open(control_params_path, 'r') as f:
            control_params = yaml.safe_load(f)

        # Merge control params into the main config
        if 'pid_params' in control_params:
            for component in config.get('components', []):
                if component.get('name') == 'pid_controller':
                    if 'properties' not in component:
                        component['properties'] = {}
                    component['properties'].update(control_params['pid_params'])
                    print(f"Merged 'pid_params' into 'pid_controller'")
                    break # Found and updated, no need to continue loop

    print(f"--- Initializing SimulationManager in {args.mode} mode ---")
    try:
        # The manager now handles config loading and preprocessing internally
        manager = SimulationManager(config=config)

        print("--- Running simulation ---")
        results_df = manager.run(mode=args.mode)

        print("\n--- Simulation Finished ---")
        print("Results (first 5 rows):")
        print(results_df.head())

    except Exception as e:
        print(f"\nAn error occurred during simulation: {e}")
        # Optionally, re-raise for debugging
        raise

if __name__ == "__main__":
    main()
