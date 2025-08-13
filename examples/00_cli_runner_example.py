import argparse
import os
from water_system_simulator.simulation_manager import SimulationManager

def main():
    """
    Main function to run a simulation from a specified case directory.
    """
    parser = argparse.ArgumentParser(description="Run a water system simulation case.")
    parser.add_argument(
        "case_path",
        type=str,
        help="Path to the case directory (e.g., 'examples/2_single_reservoir_case/')."
    )
    args = parser.parse_args()

    if not os.path.isdir(args.case_path):
        print(f"Error: Case path not found at '{args.case_path}'")
        return

    try:
        # The engine will find and load the correct files from the given path.
        # We must use the 'case_path' keyword argument.
        manager = SimulationManager(case_path=args.case_path)

        # Get duration from topology config, with a default fallback
        duration = manager.topology.get('duration', 200)
        log_prefix = os.path.basename(os.path.normpath(args.case_path))

        # Run the simulation and save the log file.
        manager.run(duration=duration, log_to_file=True, log_file_prefix=log_prefix)

    except Exception as e:
        print(f"\nAn error occurred during simulation: {e}")

if __name__ == "__main__":
    main()
