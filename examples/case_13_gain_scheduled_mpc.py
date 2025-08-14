import numpy as np
import matplotlib.pyplot as plt
import os

from water_system_simulator.simulation_manager import SimulationManager
from water_system_simulator.utils.model_conversion import integral_delay_to_ss

def get_simulation_config(controller_type: str) -> dict:
    """
    Generates the simulation configuration dictionary for a given controller type.
    """
    # --- System and Model Definitions ---
    plant_model_bank = [
        {"threshold": 300, "K": 0.008, "T": 1800},
        {"threshold": float('inf'), "K": 0.004, "T": 1800}
    ]
    controller_model_bank = plant_model_bank
    setpoint = 5.0
    dt = 10

    # --- Component Configurations ---
    components = {
        "plant": {
            "type": "PiecewiseIntegralDelayModel",
            "properties": {
                "model_bank": plant_model_bank,
                "dt": dt,
                "initial_value": 0.0
            }
        },
        "disturbance": {
            "type": "Disturbance",
            "properties": {
                "signal_type": "step",
                "step_time": 2000,
                "initial_value": 200,
                "step_value": 400
            }
        }
    }

    if controller_type == "StandardMPC":
        avg_K = np.mean([m['K'] for m in controller_model_bank])
        avg_T = np.mean([m['T'] for m in controller_model_bank])
        A_avg, B_avg = integral_delay_to_ss(avg_K, avg_T, dt)
        components["controller"] = {
            "type": "MPCController",
            "properties": {
                "A": A_avg.tolist(), "B": B_avg.tolist(), # Convert to list for YAML-like config
                "Q": [1.0], "R": [0.1], "N": 20, "setpoint": setpoint,
                "u_min": 0, "u_max": 1000
            }
        }
    elif controller_type == "GainScheduledMPC":
        components["controller"] = {
            "type": "GainScheduledMPCController",
            "properties": {
                "model_bank": controller_model_bank,
                "Q": [1.0], "R": [0.1], "N": 20, "dt": dt, "setpoint": setpoint,
                "u_min": 0, "u_max": 1000
            }
        }
    else:
        raise ValueError(f"Unknown controller type: {controller_type}")

    # --- Connections and Execution ---
    config = {
        "simulation_params": {"total_time": 10000, "dt": dt},
        "components": components,
        "connections": [
            {"source": "plant.output", "target": "controller.measured_value"},
            {"source": "disturbance.output", "target": "plant.input.inflow"},
        ],
        "execution_order": [
            # 1. Update disturbance signal
            {"component": "disturbance", "method": "step", "args": {"t": "simulation.t"}},
            # 2. GS-MPC needs the scheduling variable (disturbance) before it runs
            {
                "component": "controller", "method": "step",
                "args": {
                    "measured_value": "plant.output",
                    "scheduling_variable": "disturbance.output"
                },
                "result_to": "plant.input.control_inflow"
            } if controller_type == "GainScheduledMPC" else {
                "component": "controller", "method": "step",
                "args": {"measured_value": "plant.output"},
                "result_to": "plant.input.control_inflow"
            },
            # 3. Update the plant with all inflows
            {"component": "plant", "method": "step"}
        ],
        "logger_config": [
            "plant.output", "controller.output", "disturbance.output"
        ]
    }
    return config

def main():
    """
    Main function to run and plot the comparison of standard MPC and Gain-Scheduled MPC.
    """
    # --- Run Standard MPC Simulation ---
    print("--- Running Standard MPC Simulation ---")
    mpc_config = get_simulation_config("StandardMPC")
    manager = SimulationManager(mpc_config)
    results_mpc = manager.run()

    # --- Run Gain-Scheduled MPC Simulation ---
    print("\n--- Running Gain-Scheduled MPC Simulation ---")
    gs_mpc_config = get_simulation_config("GainScheduledMPC")
    manager = SimulationManager(gs_mpc_config)
    results_gs_mpc = manager.run()

    # --- Plot Results ---
    if not os.path.exists('results'):
        os.makedirs('results')

    plt.figure(figsize=(15, 10))
    plt.subplot(2, 1, 1)
    plt.plot(results_mpc['time'], results_mpc['plant.output'], label='Standard MPC')
    plt.plot(results_gs_mpc['time'], results_gs_mpc['plant.output'], label='Gain-Scheduled MPC', linestyle='--')
    plt.axhline(y=5.0, color='r', linestyle=':', label='Setpoint')
    plt.title('Controller Performance Comparison')
    plt.ylabel('Downstream Water Level (m)')
    plt.legend()
    plt.grid(True)

    plt.subplot(2, 1, 2)
    plt.plot(results_mpc['time'], results_mpc['controller.output'], label='Standard MPC Control Action')
    plt.plot(results_gs_mpc['time'], results_gs_mpc['controller.output'], label='Gain-Scheduled MPC Control Action', linestyle='--')
    plt.plot(results_gs_mpc['time'], results_gs_mpc['disturbance.output'], label='Inflow Disturbance', color='gray', alpha=0.7)
    plt.xlabel('Time (s)')
    plt.ylabel('Flow Rate (m^3/s)')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plot_path = 'results/gs_mpc_comparison.png'
    plt.savefig(plot_path)
    print(f"\nComparison plot saved as {plot_path}")

if __name__ == "__main__":
    main()
