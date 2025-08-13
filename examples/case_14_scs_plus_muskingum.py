import pandas as pd
import matplotlib.pyplot as plt
from water_system_simulator.simulation_manager import SimulationManager
from water_system_simulator.modeling.hydrology.sub_basin import SubBasin

def create_scs_muskingum_config():
    """
    Creates a configuration dictionary for a simulation using
    SCS runoff and Muskingum routing strategies.
    """
    # Define a simple sub-basin for the model
    sub_basin_params = {
        "area": 50.0,  # km^2
        "CN": 75,      # Curve Number for SCS model
        "K": 12,       # Muskingum K (hours)
        "x": 0.2       # Muskingum x
    }
    main_sub_basin = SubBasin(area=sub_basin_params["area"], params=sub_basin_params)

    # Define a simple rainfall event as a disturbance
    # This will be manually injected in the loop for simplicity
    rainfall_events = [0] * 10 + [10] * 2 + [20] * 2 + [15] * 2 + [5] * 2 + [0] * 50

    config = {
        "components": {
            "main_watershed": {
                "type": "SemiDistributedHydrologyModel",
                "params": {
                    "sub_basins": [main_sub_basin],
                    "strategies": {
                        "runoff": {
                            "type": "SCSRunoffModel",
                            "params": {}
                        },
                        "routing": {
                            "type": "MuskingumModel",
                            "params": {"dt": 1.0} # Pass dt for coefficient calculation
                        }
                    }
                }
            }
        },
        "simulation_params": {
            "total_time": len(rainfall_events),
            "dt": 1.0
        },
        "execution_order": [
            {
                "component": "main_watershed",
                "method": "step",
                "args": {
                    "dt": "simulation.dt",
                    "t": "simulation.t",
                    "precipitation": "main_watershed.input" # We'll set this manually
                },
                "result_to": "main_watershed.output"
            }
        ],
        "logger_config": [
            "main_watershed.output",
            "main_watershed.input"
        ]
    }
    return config, rainfall_events

def run_simulation():
    """
    Runs the simulation and plots the results.
    """
    config, rainfall_events = create_scs_muskingum_config()
    manager = SimulationManager()

    # Manually run the simulation loop to inject rainfall
    history = []
    total_time = config["simulation_params"]["total_time"]
    dt = config["simulation_params"]["dt"]

    # Build the system
    manager.config = config
    manager.components = {}
    manager._build_system()

    # Get the model
    model = manager.components["main_watershed"]

    for t_idx, t in enumerate(range(total_time)):
        rainfall_rate = rainfall_events[t_idx]
        model.input = rainfall_rate # Set precipitation input (mm/hr)

        # Execute the step
        model.step(dt=dt, t=t, precipitation=rainfall_rate)

        # Log data
        step_log = {
            "time": t,
            "rainfall (mm/hr)": rainfall_rate,
            "outflow (m3/s)": model.output
        }
        history.append(step_log)

    return pd.DataFrame(history)


if __name__ == "__main__":
    results_df = run_simulation()

    print("Simulation Results:")
    print(results_df.head())

    # Plotting the results
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Plot outflow on the primary y-axis
    color = 'tab:blue'
    ax1.set_xlabel('Time (hours)')
    ax1.set_ylabel('Outflow (m³/s)', color=color)
    ax1.plot(results_df['time'], results_df['outflow (m3/s)'], color=color, label='Outflow')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True)

    # Create a second y-axis for the rainfall
    ax2 = ax1.twinx()
    color = 'tab:gray'
    ax2.set_ylabel('Rainfall (mm/hr)', color=color)
    ax2.bar(results_df['time'], results_df['rainfall (mm/hr)'], color=color, alpha=0.5, label='Rainfall')
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.invert_yaxis() # Often helps to visualize rainfall from top

    fig.tight_layout()
    plt.title('SCS Runoff + Muskingum Routing Simulation')
    plt.savefig('scs_muskingum_simulation.png')
    print("\nPlot saved to scs_muskingum_simulation.png")
    # plt.show()
