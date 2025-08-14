import os
import numpy as np
import matplotlib.pyplot as plt

from water_system_simulator.simulation_manager import SimulationManager

def run_kf_estimation_simulation():
    """
    Defines and runs a simulation to test the ParameterKalmanFilterAgent.
    """
    # True parameters of the system we want to identify
    true_a1 = 0.85
    true_b1 = 0.5

    # Simulation Parameters
    total_time = 200
    dt = 1.0

    # Use a varying inflow signal for better identification
    times = np.arange(0, total_time, dt)
    inflow_values = 10 + 5 * np.sin(2 * np.pi * times / 50) + 3 * np.random.randn(len(times))

    kf_config = {
        "simulation_params": {
            "total_time": total_time,
            "dt": dt
        },
        "components": {
            "inflow_signal": {
                "type": "TimeSeriesDisturbance",
                "properties": {
                    "times": times.tolist(),
                    "values": inflow_values.tolist()
                }
            },
            "plant": {
                "type": "FirstOrderSystem",
                "properties": {
                    "a1": true_a1,
                    "b1": true_b1,
                }
            },
            "estimator": {
                "type": "ParameterKalmanFilterAgent",
                "properties": {
                    "initial_params": {"a1": 0.1, "b1": 0.1},
                    "process_noise_Q": 1e-6,
                    "measurement_noise_R": 0.05**2
                }
            }
        },
        "connections": [],
        "execution_order": [
            {
                "component": "inflow_signal",
                "method": "step",
                "args": {"t": "simulation.t", "dt": "simulation.dt"}
            },
            {
                "component": "plant",
                "method": "step",
                "args": {"inflow": "inflow_signal.output"},
            },
            {
                "component": "estimator",
                "method": "step",
                "args": {
                    "inflow": "inflow_signal.output",
                    "observed_outflow": "plant.output"
                },
            }
        ],
        "logger_config": [
            "estimator.state.a1",
            "estimator.state.b1",
            "plant.output",
            "inflow_signal.output"
        ]
    }

    manager = SimulationManager(config=kf_config)
    results_df = manager.run()
    return results_df, true_a1, true_b1

def plot_results(df, true_a1, true_b1):
    """Plots the parameter estimation results."""
    plt.figure(figsize=(14, 8))

    plt.subplot(2, 1, 1)
    plt.plot(df['time'], df['estimator.state.a1'], label='Estimated a1')
    plt.axhline(y=true_a1, color='r', linestyle='--', label=f'True a1 = {true_a1}')
    plt.title('Kalman Filter Parameter Estimation')
    plt.ylabel('Value of a1')
    plt.legend()
    plt.grid(True)

    plt.subplot(2, 1, 2)
    plt.plot(df['time'], df['estimator.state.b1'], label='Estimated b1')
    plt.axhline(y=true_b1, color='r', linestyle='--', label=f'True b1 = {true_b1}')
    plt.xlabel('Time (s)')
    plt.ylabel('Value of b1')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    if not os.path.exists('results'):
        os.makedirs('results')
    save_path = 'results/case_23_kf_parameter_estimation.png'
    plt.savefig(save_path)
    print(f"Plot saved to {save_path}")

if __name__ == "__main__":
    results, t_a1, t_b1 = run_kf_estimation_simulation()
    print("Simulation finished. Final estimated parameters:")
    print(results[['estimator.state.a1', 'estimator.state.b1']].iloc[-1])
    plot_results(results, t_a1, t_b1)
