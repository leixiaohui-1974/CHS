import matplotlib.pyplot as plt
import pandas as pd
from water_system_simulator.simulation_manager import SimulationManager

def run_case_01():
    """
    Runs Case 01: Open-loop response of a reservoir with constant flows.
    """
    # 1. Define the simulation configuration
    config = {
        "simulation_params": {
            "total_time": 200,
            "dt": 1
        },
        "components": {
            "inflow_dist": {
                "type": "Disturbance",
                "params": {
                    "signal_type": "constant",
                    "value": 10.0
                }
            },
            "outflow_dist": {
                "type": "Disturbance",
                "params": {
                    "signal_type": "constant",
                    "value": 5.0
                }
            },
            "reservoir1": {
                "type": "ReservoirModel",
                "params": {
                    "area": 100.0,
                    "initial_level": 5.0
                }
            }
        },
        "connections": [
            {
                "source": "inflow_dist.output",
                "target": "reservoir1.input.inflow"
            },
            {
                "source": "outflow_dist.output",
                "target": "reservoir1.input.outflow"
            }
        ],
        "execution_order": ["inflow_dist", "outflow_dist", "reservoir1"],
        "logger_config": [
            "reservoir1.state.level",
            "inflow_dist.output",
            "outflow_dist.output"
        ]
    }

    # 2. Initialize and run the simulation
    manager = SimulationManager()
    results_df = manager.run(config)

    # 3. Plot the results
    plt.figure(figsize=(10, 6))
    plt.plot(results_df['time'], results_df['reservoir1.state.level'], label='Reservoir Water Level')
    plt.title('Case 01: Reservoir Open Loop Response')
    plt.xlabel('Time (s)')
    plt.ylabel('Water Level (m)')
    plt.grid(True)
    plt.legend()

    # Save the figure
    # Ensure the 'results' directory exists
    import os
    os.makedirs("results", exist_ok=True)
    output_filename = "results/case_01_reservoir_open_loop.png"
    plt.savefig(output_filename)
    print(f"Plot saved to {output_filename}")
    # plt.show() # Comment out for non-interactive environments

    # 4. Verification
    # With inflow=10 and outflow=5, net flow is 5.
    # Level change per second = (10-5)/area = 5/100 = 0.05 m/s
    # After 200s, total change = 200 * 0.05 = 10m.
    # Final level = initial_level + 10 = 5 + 10 = 15m.
    final_level = results_df['reservoir1.state.level'].iloc[-1]
    expected_final_level = 15.0
    print(f"Final water level: {final_level:.2f} m")
    print(f"Expected final water level: {expected_final_level:.2f} m")
    assert abs(final_level - expected_final_level) < 1e-6, "Verification failed!"
    print("Verification successful!")


if __name__ == "__main__":
    run_case_01()
