import sys
import os
import matplotlib.pyplot as plt
import pandas as pd

# Adjust the path to import the SDK. The root of the package is the 'src' directory.
# This allows the relative imports within the SDK to work correctly.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'water_system_sdk', 'src')))

from water_system_simulator.simulation_manager import SimulationManager


def main():
    """
    This example demonstrates a more realistic closed-loop control system
    by introducing sensor and actuator models.

    System components:
    - A Reservoir.
    - A PID controller to regulate the reservoir's water level.
    - A LevelSensor that adds noise to the water level measurement.
    - A GateActuator that simulates the slow movement of a control gate.
    - A GateStation that releases water based on the actuator's position.
    """
    print("--- Setting up instrumented PID control simulation ---")

    # This configuration demonstrates the new "Instrument Layer" and the
    # expressive execution order.
    sdk_config = {
        "simulation_params": {
            "total_time": 2000,
            "dt": 1.0,
        },
        "components": {
            "main_reservoir": {
                "type": "ReservoirModel",
                "params": {
                    "area": 150.0,
                    "initial_level": 5.0,
                    # Constant inflow to the reservoir
                    "inflow": 10.0
                }
            },
            "outlet_gate": {
                "type": "GateStationModel",
                "params": {
                    "num_gates": 1,
                    "gate_width": 5.0,
                    "discharge_coeff": 0.6,
                    # NOTE: For this example, we assume gate_opening is a ratio (0-1)
                    # directly matching the actuator output. A real system would
                    # scale this to a physical height.
                }
            },
            "level_sensor": {
                "type": "LevelSensor",
                "params": {
                    "noise_std_dev": 0.05 # 5cm of noise
                }
            },
            "gate_actuator": {
                "type": "GateActuator",
                "params": {
                    "travel_time": 300.0, # 5 minutes for full travel
                    "initial_position": 0.1
                }
            },
            "pid_controller": {
                "type": "PIDController",
                "params": {
                    "Kp": 0.8,
                    "Ki": 0.03,
                    "Kd": 0.1,
                    "set_point": 10.0,
                    "output_min": 0.0,
                    "output_max": 1.0 # Output is a gate position command
                }
            }
        },
        "connections": [
            # The noisy sensor measurement is the input to the PID controller
            {
                "source": "level_sensor.measured_value",
                "target": "pid_controller.input.error_source"
            },
            # The flow from the gate is the outflow of the reservoir
            {
                "source": "outlet_gate.flow",
                "target": "main_reservoir.input.outflow"
            }
        ],
        "execution_order": [
            # 1. Measure the true value from the reservoir. The result is stored
            #    in the sensor's 'measured_value' attribute.
            {
                "component": "level_sensor",
                "method": "measure",
                "args": { "true_value": "main_reservoir.state.level" }
            },
            # 2. The PID controller runs. Its input is already connected via the
            #    'connections' block.
            "pid_controller",
            # 3. The actuator moves based on the PID's command.
            {
                "component": "gate_actuator",
                "method": "step",
                "args": {
                    "command": "pid_controller.state.output",
                    "dt": "simulation.dt"
                }
            },
            # 4. The gate's flow is calculated based on the actuator's actual
            #    position and the reservoir's current water level.
            {
                "component": "outlet_gate",
                "method": "step",
                "args": {
                    "upstream_level": "main_reservoir.state.level",
                    "gate_opening": "gate_actuator.current_position"
                }
            },
            # 5. Finally, the reservoir's state is updated.
            "main_reservoir"
        ],
        "logger_config": [
            "main_reservoir.state.level",
            "level_sensor.measured_value",
            "pid_controller.set_point",
            "gate_actuator.current_position",
            "pid_controller.state.output"
        ]
    }

    print("--- Initializing SimulationManager ---")
    # The SimulationManager now needs the config passed at run time
    manager = SimulationManager()

    print("--- Running simulation ---")
    results_df = manager.run(config=sdk_config)

    print("--- Simulation finished. Plotting results. ---")

    # --- Plotting ---
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12), sharex=True)

    # Subplot 1: Water Level Control
    ax1.plot(results_df["time"], results_df["main_reservoir.state.level"], label="True Water Level", color='blue', linewidth=2)
    ax1.plot(results_df["time"], results_df["level_sensor.measured_value"], label="Measured Water Level", color='skyblue', linestyle='--', alpha=0.7)
    ax1.axhline(y=sdk_config["components"]["pid_controller"]["params"]["set_point"], color='r', linestyle='--', label="Setpoint")
    ax1.set_title("Reservoir Level Control with Sensor Noise")
    ax1.set_ylabel("Water Level (m)")
    ax1.legend()
    ax1.grid(True)

    # Subplot 2: Actuator and PID Output
    ax2.plot(results_df["time"], results_df["pid_controller.state.output"], label="PID Output (Commanded Position)", color='green', linestyle='--')
    ax2.plot(results_df["time"], results_df["gate_actuator.current_position"], label="Actuator Position (Actual)", color='purple', linewidth=2)
    ax2.set_title("Gate Actuator Response")
    ax2.set_ylabel("Gate Position (0-1)")
    ax2.set_xlabel("Time (s)")
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()

    # Save the plot
    output_filename = "case_04_instrumented_pid.png"
    plt.savefig(output_filename)
    print(f"Plot saved to {output_filename}")

    # Check for simulation success
    final_level = results_df["main_reservoir.state.level"].iloc[-1]
    set_point = sdk_config["components"]["pid_controller"]["params"]["set_point"]
    if abs(final_level - set_point) < 0.5:
        print("Example script finished successfully: Final level is close to setpoint.")
    else:
        print(f"Warning: Final level ({final_level:.2f}) is not close to setpoint ({set_point:.2f}).")


if __name__ == "__main__":
    main()
