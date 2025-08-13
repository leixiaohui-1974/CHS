import os
from water_system_simulator.engine import Simulator

def main():
    """
    Main function to run the complex Case 6 simulation.
    """
    case_path = 'examples/6_complex_tunnel_pipeline_case/'

    if not os.path.isdir(case_path):
        print(f"Error: Case path not found at '{case_path}'")
        return

    try:
        # This case has multiple controllers defined in its control_parameters.yaml
        # The engine's current logic will apply the parameters based on the component name.
        # e.g., the 'siphon_pid' component will get the 'siphon_pid_params'.
        sim = Simulator(case_path)

        duration = 400
        dt = 1.0
        log_prefix = os.path.basename(os.path.normpath(case_path))

        sim.run(duration=duration, dt=dt, log_file_prefix=log_prefix)

    except Exception as e:
        print(f"\nAn error occurred during simulation: {e}")

if __name__ == "__main__":
    main()
