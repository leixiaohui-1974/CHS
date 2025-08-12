import pandas as pd
import matplotlib.pyplot as plt
import os

from water_system_simulator.engine import Simulator

def run_control_simulations():
    """
    Runs PID and MPC control simulations for the two-tank system and compares the results.
    """
    print("\n--- Running Two-Tank Control Simulations ---")
    duration = 200
    dt = 1.0

    # --- Run PID Simulation ---
    print("\nRunning PID simulation...")
    pid_config = 'configs/case2_pid_topology.yml'
    pid_log = 'case2_pid_log.csv'
    try:
        pid_sim = Simulator(pid_config)
        pid_sim.run(duration=duration, dt=dt, log_file=pid_log)
    except Exception as e:
        print(f"PID simulation failed: {e}")
        return

    # --- Run MPC Simulation ---
    print("\nRunning MPC simulation...")
    mpc_config = 'configs/case2_mpc_topology.yml'
    mpc_log = 'case2_mpc_log.csv'
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

        # Plot water levels of the second tank
        plt.plot(df_pid['time'], df_pid['tank2.storage'], label='PID Controlled Level (Tank 2)', color='blue')
        plt.plot(df_mpc['time'], df_mpc['tank2.storage'], label='MPC Controlled Level (Tank 2)', color='green')
        plt.axhline(y=5.0, color='r', linestyle='--', label='Setpoint')

        # Optionally plot the first tank's level to see its behavior
        plt.plot(df_pid['time'], df_pid['tank1.storage'], label='PID - Tank 1 Level', color='lightblue', linestyle=':')
        plt.plot(df_mpc['time'], df_mpc['tank1.storage'], label='MPC - Tank 1 Level', color='lightgreen', linestyle=':')

        plt.title('Case 2: PID vs. MPC Control for a Two-Tank System')
        plt.xlabel('Time (s)')
        plt.ylabel('Water Level (m)')
        plt.legend()
        plt.grid(True)

        plot_file = 'case2_pid_vs_mpc_comparison.png'
        plt.savefig(f"results/{plot_file}")
        print(f"Comparison plot saved to results/{plot_file}")

    except FileNotFoundError as e:
        print(f"Could not find log file for plotting: {e}")


def main():
    """Main function to run Case Study 2."""
    if not os.path.exists('results'):
        os.makedirs('results')
    run_control_simulations()


if __name__ == "__main__":
    main()
