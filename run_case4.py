import os
from water_system_simulator.engine import Simulator

def main():
    """
    Main function to run the complex Case 4 simulation.
    """
    case_path = 'examples/5_one_gate_two_channels_case/'

    if not os.path.isdir(case_path):
        print(f"Error: Case path not found at '{case_path}'")
        return

    try:
        sim = Simulator(case_path)

        duration = 250
        dt = 1.0
        log_prefix = os.path.basename(os.path.normpath(case_path))

        sim.run(duration=duration, dt=dt, log_file_prefix=log_prefix)

    except Exception as e:
        print(f"\nAn error occurred during simulation: {e}")

if __name__ == "__main__":
    main()
