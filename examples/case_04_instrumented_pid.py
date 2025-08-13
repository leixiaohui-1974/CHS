import matplotlib.pyplot as plt
from water_system_simulator.simulation_manager import SimulationManager
import os
import sys

# This is a temporary solution to make the script runnable without installing the package.
# A proper setup would involve installing the package in editable mode.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'water_system_sdk', 'src')))


def run_case_04():
    """
    Runs Case 04: Instrumented PID control of a single reservoir.
    This case demonstrates:
    - A LevelSensor with noise.
    - A GateActuator with a travel time.
    - A more complex execution logic using dictionaries.
    """
    # 1. Define the simulation configuration
    config = {
        "simulation_params": {
            "total_time": 1000,
            "dt": 1.0
        },
        "components": {
            "outflow_dist": {
                "type": "Disturbance",
                "params": {"signal_type": "constant", "value": 8.0}
            },
            "reservoir": {
                "type": "ReservoirModel",
                "params": {"area": 150.0, "initial_level": 5.0}
            },
            "level_sensor": {
                "type": "LevelSensor",
                "params": {"noise_std_dev": 0.15} # 15cm stdev noise
            },
            "pid": {
                "type": "PIDController",
                "params": {
                    "Kp": 0.05, "Ki": 0.01, "Kd": 0.01,
                    "set_point": 10.0,
                    "output_min": 0.0, "output_max": 1.0 # PID output is gate position command
                }
            },
            "gate_actuator": {
                "type": "GateActuator",
                "params": {
                    "travel_time": 120.0, # 2 minutes for full travel
                    "initial_position": 0.1
                }
            },
            "inflow_gate": {
                "type": "GateStationModel",
                "params": {
                    "num_gates": 2,
                    "gate_width": 2.0,
                    "discharge_coeff": 0.8,
                }
            }
        },
        # NOTE: Using the expressive dictionary-based execution order exclusively.
        "execution_order": [
            # 1. Measure the true reservoir level with the noisy sensor.
            #    The result is stored in `level_sensor.output`.
            {
                "component": "level_sensor",
                "method": "step",
                "args": {"true_value": "reservoir.output"}
            },
            # 2. PID calculates a new target gate position based on the *sensed* level.
            {
                "component": "pid",
                "method": "step",
                "args": {
                    "error_source": "level_sensor.output",
                    "dt": "simulation.dt"
                }
            },
            # 3. Actuator moves the gate towards the target position over dt.
            #    The result is stored in `gate_actuator.output`.
            {
                "component": "gate_actuator",
                "method": "step",
                "args": {"command": "pid.output", "dt": "simulation.dt"}
            },
            # 4. Gate model calculates inflow based on actuator's actual position
            #    and the reservoir's own level (as upstream_level).
            #    We assume the actuator's 0-1 output can be used as 'gate_opening'.
            #    The result is stored in `inflow_gate.output` and then copied to reservoir input.
            {
                "component": "inflow_gate",
                "method": "step",
                "args": {
                    "upstream_level": 12.0,
                    "gate_opening": "gate_actuator.output"
                },
                "result_to": "reservoir.input.inflow"
            },
            # 5. Update the disturbance and apply it as outflow.
            {
                "component": "outflow_dist",
                "method": "step",
                "args": {"t": "simulation.t"},
                "result_to": "reservoir.input.demand_outflow"
            },
            # 6. Finally, update the reservoir itself using the new inflow/outflow.
            {
                "component": "reservoir",
                "method": "step",
                "args": {"dt": "simulation.dt"}
            }
        ],
        "logger_config": [
            "reservoir.output",
            "level_sensor.output",
            "pid.output",
            "gate_actuator.output",
            "inflow_gate.output"
        ]
    }

    # 2. Initialize and run the simulation
    manager = SimulationManager()
    results_df = manager.run(config)

    # 3. Plot the results
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)

    # Subplot 1: Water Levels
    ax1.plot(results_df['time'], results_df['reservoir.output'], 'b-', linewidth=2, label='True Water Level (m)')
    ax1.plot(results_df['time'], results_df['level_sensor.output'], 'k.', markersize=2, alpha=0.8, label='Sensed Water Level (m)')
    ax1.axhline(y=config['components']['pid']['params']['set_point'], color='r', linestyle='--', label='Setpoint (10m)')
    ax1.set_ylabel('Water Level (m)')
    ax1.legend()
    ax1.grid(True)
    ax1.set_title('Case 04: Instrumented PID Control Simulation')

    # Subplot 2: Actuator and Controller
    ax2.plot(results_df['time'], results_df['pid.output'], 'g--', label='PID Command (Target Position)')
    ax2.plot(results_df['time'], results_df['gate_actuator.output'], 'm-', linewidth=2, label='Actual Gate Position (0-1)')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Normalized Position')
    ax2.legend(loc='upper left')
    ax2.grid(True)

    # Second y-axis for inflow
    ax2b = ax2.twinx()
    ax2b.plot(results_df['time'], results_df['inflow_gate.output'], 'c:', label='Inflow (m³/s)')
    ax2b.set_ylabel('Flow Rate (m³/s)', color='c')
    ax2b.tick_params(axis='y', labelcolor='c')
    ax2b.legend(loc='upper right')

    fig.tight_layout()

    # Save the figure
    os.makedirs("results", exist_ok=True)
    output_filename = "results/case_04_instrumented_pid.png"
    plt.savefig(output_filename)
    print(f"Plot saved to {output_filename}")

    # Verification
    final_level = results_df['reservoir.output'].iloc[-1]
    set_point = config['components']['pid']['params']['set_point']
    print(f"Final water level: {final_level:.2f} m")
    print(f"Setpoint: {set_point:.2f} m")
    # Check if the level settles close to the setpoint (with some tolerance for noise)
    assert abs(final_level - set_point) < 0.5, "Verification failed: Level did not settle near setpoint."

    final_inflow = results_df['inflow_gate.output'].iloc[-1]
    final_outflow = config['components']['outflow_dist']['params']['value']
    print(f"Final inflow: {final_inflow:.2f} m³/s")
    print(f"Final outflow: {final_outflow:.2f} m³/s")
    # Check if inflow stabilizes to match outflow (with some tolerance for noise)
    assert abs(final_inflow - final_outflow) < 0.5, "Verification failed: Inflow did not stabilize to match outflow."

    print("Verification successful!")


if __name__ == "__main__":
    run_case_04()
