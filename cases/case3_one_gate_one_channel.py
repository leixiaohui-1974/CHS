import pandas as pd
import matplotlib.pyplot as plt
import os

from water_system_simulator.engine import Simulator

def run_control_simulations():
    """
    Runs PID and MPC control simulations for the one-gate-one-channel system.
    """
    print("\n--- Running Case 3: One Gate, One Channel Simulations ---")
    duration = 200
    dt = 1.0

    # --- Run PID Simulation ---
    print("\nRunning PID simulation...")
    pid_config = 'configs/case3_pid_topology.yml'
    pid_log = 'case3_pid_log.csv'
    try:
        pid_sim = Simulator(pid_config, 'configs/case3_disturbances.csv')
        pid_sim.run(duration=duration, dt=dt, log_file=pid_log)
    except Exception as e:
        print(f"PID simulation failed: {e}")
        return

    # --- Run MPC Simulation ---
    print("\nRunning MPC simulation...")
    mpc_config = 'configs/case3_mpc_topology.yml'
    mpc_log = 'case3_mpc_log.csv'
    try:
        mpc_sim = Simulator(mpc_config, 'configs/case3_disturbances.csv')
        mpc_sim.run(duration=duration, dt=dt, log_file=mpc_log)
    except Exception as e:
        print(f"MPC simulation failed: {e}")
        return

    # --- Plot Comparison ---
    print("\nPlotting comparison...")
    try:
        df_pid = pd.read_csv(f"results/{pid_log}")
        df_mpc = pd.read_csv(f"results/{mpc_log}")

        fig, ax1 = plt.subplots(figsize=(14, 8))

        # Plot water level on primary y-axis
        color = 'tab:blue'
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Gate Forebay Level (m)', color=color)
        ax1.plot(df_pid['time'], df_pid['channel.output'], label='Gate Forebay Level (PID)', color='blue')
        ax1.plot(df_mpc['time'], df_mpc['channel.output'], label='Gate Forebay Level (MPC)', color='green')
        ax1.axhline(y=10.0, color='r', linestyle='--', label='Setpoint')
        ax1.tick_params(axis='y', labelcolor=color)
        ax1.legend(loc='upper left')
        ax1.grid(True)

        # Plot disturbance inflow on secondary y-axis
        ax2 = ax1.twinx()
        color = 'tab:gray'
        ax2.set_ylabel('Upstream Inflow (m^3/s)', color=color)
        ax2.plot(df_pid['time'], df_pid['inflow_to_channel.output'], label='Upstream Inflow', color=color, linestyle=':')
        ax2.tick_params(axis='y', labelcolor=color)
        ax2.legend(loc='upper right')

        fig.tight_layout()
        plt.title('Case 3: PID vs. MPC for Upstream Level Control')

        plot_file = 'case3_pid_vs_mpc_comparison.png'
        plt.savefig(f"results/{plot_file}")
        print(f"Comparison plot saved to results/{plot_file}")

    except FileNotFoundError as e:
        print(f"Could not find log file for plotting: {e}")


def main():
    """Main function to run Case Study 3."""
    if not os.path.exists('results'):
        os.makedirs('results')
    run_control_simulations()


if __name__ == "__main__":
    main()
