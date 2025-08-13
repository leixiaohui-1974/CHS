import matplotlib.pyplot as plt
from water_system_simulator.simulation_manager import SimulationManager
import os

def run_case_03():
    """
    Runs Case 03: Closed-loop PID control of a single water tank.
    """
    # 1. Define the simulation configuration
    config = {
        "simulation_params": {
            "total_time": 500,
            "dt": 1.0
        },
        "components": {
            "outflow_dist": {
                "type": "Disturbance",
                "params": {
                    "signal_type": "constant",
                    "value": 10.0 # Constant outflow demand
                }
            },
            "reservoir": {
                "type": "ReservoirModel",
                "params": {
                    "area": 100.0,
                    "initial_level": 2.0
                }
            },
            "pid": {
                "type": "PIDController",
                "params": {
                    "Kp": 2.5, "Ki": 0.08, "Kd": 1.5,
                    "set_point": 10.0, # Target water level
                    "output_min": 0.0 # Inflow cannot be negative
                }
            }
        },
        "connections": [
            # Connect PID output to reservoir inflow
            {
                "source": "pid.state.output",
                "target": "reservoir.input.inflow"
            },
            # Connect disturbance to reservoir outflow
            {
                "source": "outflow_dist.output",
                "target": "reservoir.input.outflow"
            },
            # Feedback loop: connect reservoir level to PID input
            {
                "source": "reservoir.state.level",
                "target": "pid.input.error_source"
            }
        ],
        # Execution order:
        # 1. Update reservoir with flows from previous step.
        # 2. PID calculates new inflow based on new reservoir state.
        # 3. Disturbance is stateless but we keep it in the loop.
        "execution_order": ["reservoir", "pid", "outflow_dist"],
        "logger_config": [
            "reservoir.state.level",
            "pid.state.output",
        ]
    }

    # 2. Initialize and run the simulation
    manager = SimulationManager()
    results_df = manager.run(config)

    # 3. Plot the results
    fig, ax1 = plt.subplots(figsize=(12, 7))

    # Plot water level
    ax1.plot(results_df['time'], results_df['reservoir.state.level'], 'b-', label='Water Level (m)')
    ax1.axhline(y=config['components']['pid']['params']['set_point'], color='r', linestyle='--', label='Setpoint (10m)')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Water Level (m)', color='b')
    ax1.tick_params(axis='y', labelcolor='b')
    ax1.grid(True)

    # Plot controller output on a second y-axis
    ax2 = ax1.twinx()
    ax2.plot(results_df['time'], results_df['pid.state.output'], 'g:', label='Controller Output (Inflow)')
    ax2.set_ylabel('Controller Output (m³/s)', color='g')
    ax2.tick_params(axis='y', labelcolor='g')

    # Combine legends
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='lower right')

    plt.title('Case 03: Single Tank PID Closed-Loop Control')
    fig.tight_layout()

    # Save the figure
    os.makedirs("results", exist_ok=True)
    output_filename = "results/case_03_single_tank_pid.png"
    plt.savefig(output_filename)
    print(f"Plot saved to {output_filename}")

    # Verification
    final_level = results_df['reservoir.state.level'].iloc[-1]
    set_point = config['components']['pid']['params']['set_point']
    print(f"Final water level: {final_level:.2f} m")
    print(f"Setpoint: {set_point:.2f} m")
    # Check if the level settles close to the setpoint
    assert abs(final_level - set_point) < 0.1, "Verification failed: Level did not settle at setpoint."

    final_inflow = results_df['pid.state.output'].iloc[-1]
    final_outflow = config['components']['outflow_dist']['params']['value']
    print(f"Final inflow: {final_inflow:.2f} m³/s")
    print(f"Final outflow: {final_outflow:.2f} m³/s")
    # Check if inflow stabilizes to match outflow
    assert abs(final_inflow - final_outflow) < 0.1, "Verification failed: Inflow did not stabilize to match outflow."

    print("Verification successful!")

if __name__ == "__main__":
    run_case_03()
