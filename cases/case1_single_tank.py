import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

from water_system_simulator.engine import Simulator
from water_system_simulator.identification.least_squares import identify_time_constant
from water_system_simulator.modeling.storage_models import FirstOrderInertiaModel

def run_identification_test(dt: float):
    """
    Generates data and identifies the time constant of the tank model.
    """
    print("\n--- Running Identification Test ---")
    # True parameter
    true_time_constant = 5.0
    tank = FirstOrderInertiaModel(initial_storage=0.5, time_constant=true_time_constant)

    # Generate data with a known inflow pattern
    duration = 50
    inflow_data = np.sin(np.linspace(0, 10, int(duration/dt))) + 1.0
    storage_data = []

    for inflow in inflow_data:
        storage_data.append(tank.storage)
        tank.step(inflow) # dt is 1.0 here, but the model doesn't use it.
                          # The identification function needs the correct dt.

    storage_data = np.array(storage_data)

    # Identify the time constant
    try:
        identified_T = identify_time_constant(storage_data, inflow_data, dt)
        print(f"True Time Constant: {true_time_constant}")
        print(f"Identified Time Constant: {identified_T:.4f}")
        assert np.isclose(true_time_constant, identified_T, rtol=1e-3), "Identification failed!"
        print("Identification successful.")
    except (RuntimeError, ValueError) as e:
        print(f"Identification failed: {e}")


def run_control_simulations():
    """
    Runs PID and MPC control simulations and compares the results.
    """
    print("\n--- Running Control Simulations ---")
    duration = 100
    dt = 1.0

    # --- Run PID Simulation ---
    print("\nRunning PID simulation...")
    pid_config = 'configs/case1_topology.yml'
    pid_log = 'case1_pid_log.csv'
    try:
        pid_sim = Simulator(pid_config)
        pid_sim.run(duration=duration, dt=dt, log_file=pid_log)
    except Exception as e:
        print(f"PID simulation failed: {e}")
        return

    # --- Run MPC Simulation ---
    print("\nRunning MPC simulation...")
    mpc_config = 'configs/case1_mpc_topology.yml'
    mpc_log = 'case1_mpc_log.csv'
    try:
        mpc_sim = Simulator(mpc_config)
        mpc_sim.run(duration=duration, dt=dt, log_file=mpc_log)
    except Exception as e:
        print(f"MPC simulation failed: {e}")
        return

    # --- Plot Comparison ---
    print("\nPlotting comparison...")
    try:
        df_pid = pd.read_csv(f"results/{pid_log}")
        df_mpc = pd.read_csv(f"results/{mpc_log}")

        plt.figure(figsize=(14, 8))

        # Plot water levels
        plt.plot(df_pid['time'], df_pid['tank1.storage'], label='PID Controlled Level', color='blue')
        plt.plot(df_mpc['time'], df_mpc['tank1.storage'], label='MPC Controlled Level', color='green')
        plt.axhline(y=1.0, color='r', linestyle='--', label='Setpoint')

        plt.title('Case 1: PID vs. MPC Control for a Single Tank')
        plt.xlabel('Time (s)')
        plt.ylabel('Water Level (m)')
        plt.legend()
        plt.grid(True)

        plot_file = 'case1_pid_vs_mpc_comparison.png'
        plt.savefig(f"results/{plot_file}")
        print(f"Comparison plot saved to results/{plot_file}")

    except FileNotFoundError as e:
        print(f"Could not find log file for plotting: {e}")


def main():
    """Main function to run Case Study 1."""
    # Ensure results directory exists
    if not os.path.exists('results'):
        os.makedirs('results')

    run_identification_test(dt=1.0)
    run_control_simulations()


if __name__ == "__main__":
    main()
