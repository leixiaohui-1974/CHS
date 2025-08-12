import pandas as pd
import matplotlib.pyplot as plt
import os

from water_system_simulator.engine import Simulator

def run_simulation(config_path: str, log_file: str, duration: int, dt: float):
    """Helper function to run a single simulation."""
    print(f"\n--- Running simulation for {config_path} ---")
    disturbance_path = 'configs/case4_disturbances.csv'
    try:
        sim = Simulator(config_path, disturbance_path)
        sim.run(duration=duration, dt=dt, log_file=log_file)
        print(f"Simulation successful. Log saved to results/{log_file}")
        return True
    except Exception as e:
        print(f"Simulation failed for {config_path}: {e}")
        return False

def main():
    """Main function to run all Case Study 4 simulations and compare them."""
    if not os.path.exists('results'):
        os.makedirs('results')

    duration = 250
    dt = 1.0

    # Define all simulation configurations
    simulations = {
        "Upstream PID": "case4_upstream_pid_topology.yml",
        "Downstream PID": "case4_downstream_pid_topology.yml",
        "Mixed PID": "case4_mixed_pid_topology.yml",
        "MPC": "case4_mpc_topology.yml"
    }

    # Run all simulations
    for name, config_file in simulations.items():
        log_file = f"case4_{name.lower().replace(' ', '_')}_log.csv"
        run_simulation(f"configs/{config_file}", log_file, duration, dt)

    # --- Plot Comparison ---
    print("\nPlotting final comparison...")
    try:
        plt.style.use('seaborn-v0_8-whitegrid')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12), sharex=True)
        fig.suptitle('Case 4: Comparison of Control Strategies', fontsize=16)

        colors = {'Upstream PID': 'blue', 'Downstream PID': 'orange', 'Mixed PID': 'purple', 'MPC': 'green'}

        # Plot Upstream Level
        ax1.set_title('Upstream Water Level (Gate Forebay)')
        ax1.set_ylabel('Water Level (m)')
        ax1.axhline(y=10.0, color='r', linestyle='--', label='Upstream Setpoint')

        # Plot Downstream Level
        ax2.set_title('Downstream Channel Water Level')
        ax2.set_ylabel('Water Level (m)')
        ax2.axhline(y=8.0, color='r', linestyle='--', label='Downstream Setpoint')
        ax2.set_xlabel('Time (s)')

        # Load data and plot for each simulation
        for name, config_file in simulations.items():
            log_file = f"results/case4_{name.lower().replace(' ', '_')}_log.csv"
            if os.path.exists(log_file):
                df = pd.read_csv(log_file)
                ax1.plot(df['time'], df['upstream_channel.output'], label=name, color=colors[name], alpha=0.8)
                ax2.plot(df['time'], df['downstream_channel.output'], label=name, color=colors[name], alpha=0.8)

        ax1.legend()
        ax1.grid(True)
        ax2.legend()
        ax2.grid(True)

        plot_file = 'case4_all_controllers_comparison.png'
        plt.savefig(f"results/{plot_file}")
        print(f"Final comparison plot saved to results/{plot_file}")

    except Exception as e:
        print(f"Failed to generate comparison plot: {e}")


if __name__ == "__main__":
    main()
