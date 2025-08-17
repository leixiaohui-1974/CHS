import matplotlib.pyplot as plt

# The 'chs_sdk' package has been installed in editable mode.
# This allows us to import directly from the package, which is the standard
# and more robust way to use an installed library.
from chs_sdk.simulation_manager import SimulationManager
from chs_sdk.simulation_builder import SimulationBuilder


def main():
    """
    This example demonstrates how to use the SDK to simulate a single
    reservoir whose water level is controlled by a PID controller,
    using the new SimulationBuilder for configuration.
    """
    print("--- Setting up single reservoir PID control simulation using SimulationBuilder ---")

    # Use the builder to construct the configuration fluently.
    # This is more readable and less error-prone than a large dictionary.
    builder = SimulationBuilder()
    sdk_config = (builder
        .set_simulation_params(total_time=1000, dt=1.0)
        .add_component(
            name="main_reservoir",
            component_type="ReservoirModel",
            params={"area": 100.0, "initial_level": 5.0}
        )
        .add_component(
            name="level_controller",
            component_type="PIDController",
            params={
                "Kp": 0.5, "Ki": 0.02, "Kd": 0.01,
                "set_point": 10.0, "output_min": 0
            }
        )
        .add_connection(
            source="main_reservoir.state.level",
            target="level_controller.input.error_source"
        )
        .add_connection(
            source="level_controller.state.output",
            target="main_reservoir.input.inflow"
        )
        .set_execution_order(["level_controller", "main_reservoir"])
        .configure_logger([
            "main_reservoir.state.level",
            "level_controller.state.output",
            "level_controller.set_point"
        ])
        .build()
    )

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
