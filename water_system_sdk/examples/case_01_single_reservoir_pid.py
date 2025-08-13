import sys
import os
import matplotlib.pyplot as plt

# Adjust the path to import the SDK
# This is a common pattern for running examples without installing the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.water_system_simulator.simulation_manager import SimulationManager

def main():
    """
    This example demonstrates how to use the SDK to simulate a single
    reservoir whose water level is controlled by a PID controller.
    """
    print("--- Setting up single reservoir PID control simulation ---")

    # This configuration dictionary is the "API" for the simulation SDK.
    # It defines all components, their parameters, and how they are connected.
    sdk_config = {
        "simulation_params": {
            "total_time": 1000,
            "dt": 1.0
        },
        "components": {
            "main_reservoir": {
                "type": "ReservoirModel",
                "params": {
                    "area": 100.0,
                    "initial_level": 5.0
                }
            },
            "level_controller": {
                "type": "PIDController",
                "params": {
                    "Kp": 0.5,
                    "Ki": 0.02,
                    "Kd": 0.01,
                    "set_point": 10.0,
                    "output_min": 0 # Inflow can't be negative
                }
            }
        },
        "connections": [
            # The water level of the reservoir is the input to the PID controller
            {
                "source": "main_reservoir.state.level",
                "target": "level_controller.input.error_source"
            },
            # The output of the PID controller is the inflow to the reservoir
            {
                "source": "level_controller.state.output",
                "target": "main_reservoir.input.inflow"
            }
        ],
        "execution_order": [
            "level_controller",
            "main_reservoir"
        ],
        "logger_config": [
            "main_reservoir.state.level",
            "level_controller.state.output",
            "level_controller.set_point" # Log the setpoint for plotting
        ]
    }

    print("--- Initializing SimulationManager ---")
    manager = SimulationManager(config=sdk_config)

    print("--- Running simulation ---")
    results_df = manager.run()

    print("--- Simulation finished. Plotting results. ---")

    # --- Plotting ---
    plt.figure(figsize=(12, 8))

    # Plot water level
    plt.plot(results_df["time"], results_df["main_reservoir.state.level"], label="Reservoir Water Level", color='blue')

    # Plot setpoint
    # We get the setpoint value from the logger_config.
    # It's constant, so we can plot it as a horizontal line.
    set_point_value = sdk_config["components"]["level_controller"]["params"]["set_point"]
    plt.axhline(y=set_point_value, color='r', linestyle='--', label="Setpoint")

    plt.title("Reservoir Level PID Control Simulation")
    plt.xlabel("Time (s)")
    plt.ylabel("Water Level (m)")
    plt.legend()
    plt.grid(True)

    # Save the plot
    output_filename = "reservoir_pid_simulation.png"
    plt.savefig(output_filename)

    print(f"Plot saved to {output_filename}")
    print("Example script finished successfully.")

if __name__ == "__main__":
    main()
