"""
Main entry point for the water system simulation product.
"""
import argparse
from water_system_simulator.engine import Simulator
import matplotlib.pyplot as plt
import pandas as pd

def main():
    """
    Main function to run a simulation from configuration files.
    """
    # For now, we will hardcode the paths for testing case 1.
    # Later, this can be replaced with command-line argument parsing.
    topology_path = 'configs/case1_topology.yml'
    disturbance_path = 'configs/disturbances.csv'
    log_file = 'case1_simulation_log.csv'

    # Instantiate and run the simulator
    try:
        sim = Simulator(topology_path, disturbance_path)
        sim.run(duration=100, dt=1.0, log_file=log_file)

        # Plot the results for verification
        print("\nPlotting results...")
        df = pd.read_csv(f"results/{log_file}")

        plt.figure(figsize=(12, 6))
        plt.plot(df['time'], df['tank1.storage'], label='Tank 1 Storage (Water Level)')
        plt.axhline(y=1.0, color='r', linestyle='--', label='Setpoint')
        plt.title('Case 1: Single-Tank PID Control')
        plt.xlabel('Time (s)')
        plt.ylabel('Water Level (m)')
        plt.legend()
        plt.grid(True)
        plot_file = 'case1_results.png'
        plt.savefig(f"results/{plot_file}")
        print(f"Plot saved to results/{plot_file}")
        # plt.show() # Cannot show plot in this environment

    except (FileNotFoundError, ValueError, ImportError, AttributeError) as e:
        print(f"\nAn error occurred during simulation: {e}")


if __name__ == "__main__":
    main()
