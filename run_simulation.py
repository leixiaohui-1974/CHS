import argparse
import os
from water_system_simulator.engine import Simulator

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
        # The engine will find and load the correct files.
        # This generic runner can be expanded to select different topologies
        # or controller params from within the case directory.
        sim = Simulator(args.case_path)

        duration = 200
        dt = 1.0
        log_prefix = os.path.basename(os.path.normpath(args.case_path))

        sim.run(duration=duration, dt=dt, log_file_prefix=log_prefix)

    except Exception as e:
        print(f"\nAn error occurred during simulation: {e}")

if __name__ == "__main__":
    main()
