import sys
import os
import matplotlib.pyplot as plt

# This is a temporary solution to allow imports from the project root.
# This should be replaced by a proper packaging solution.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from water_system_sdk.src.water_system_simulator.modeling.hydrology.sub_basin import SubBasin
from water_system_sdk.src.water_system_simulator.modeling.hydrology.semi_distributed import SemiDistributedHydrologyModel

def run_simulation():
    """
    This example demonstrates how to set up and run a simulation
    with the SemiDistributedHydrologyModel.
    """
    # 1. Define Sub-Basin configurations
    # Parameters for a Xinanjiang runoff model and a Muskingum routing model
    sub_basin_1_params = {
        "area": 50.0,  # km^2
        "initial_state": {
            "runoff": {"initial_W": 50},
            "routing": {"initial_inflow": 0.0, "initial_outflow": 0.0}
        },
        "runoff_params": {"WM": 100, "B": 0.3, "IM": 0.05},
        "routing_params": {"K": 12, "x": 0.2, "dt": 1}
    }
    sub_basin_2_params = {
        "area": 75.0,  # km^2
        "initial_state": {
            "runoff": {"initial_W": 60},
            "routing": {"initial_inflow": 0.0, "initial_outflow": 0.0}
        },
        "runoff_params": {"WM": 120, "B": 0.2, "IM": 0.1},
        "routing_params": {"K": 15, "x": 0.25, "dt": 1}
    }

    # 2. Create SubBasin objects
    sub_basin_1 = SubBasin(**sub_basin_1_params)
    sub_basin_2 = SubBasin(**sub_basin_2_params)

    # 3. Create the main hydrological model
    watershed_model = SemiDistributedHydrologyModel(sub_basins=[sub_basin_1, sub_basin_2])

    # 4. Set up simulation time and input data
    dt = 1.0  # hours
    simulation_duration = 72  # hours
    timesteps = int(simulation_duration / dt)

    # Simple rainfall event: 10 mm/hr for 5 hours, then 0
    precipitation_ts = [10.0] * 5 + [0.0] * (timesteps - 5)
    evaporation_ts = [0.1] * timesteps # Constant evaporation

    # 5. Run the simulation
    outflows = []
    for i in range(timesteps):
        # The model's step function receives inputs as keyword arguments
        outflow = watershed_model.step(dt=dt, t=i*dt, precipitation=precipitation_ts[i], evaporation=evaporation_ts[i])
        outflows.append(outflow)

    # 6. Print and plot results
    print("Simulation finished.")
    print("Final Outflow:", outflows[-1], "m^3/s")

    plt.figure(figsize=(12, 6))
    plt.plot(range(timesteps), outflows, label='Total Watershed Outflow')
    plt.xlabel('Time (hours)')
    plt.ylabel('Outflow (m^3/s)')
    plt.title('Semi-Distributed Hydrological Model Simulation')

    # Create a second y-axis for precipitation
    ax2 = plt.gca().twinx()
    ax2.bar(range(timesteps), precipitation_ts, width=1.0, color='b', alpha=0.3, label='Precipitation')
    ax2.set_ylabel('Precipitation (mm/hr)')

    plt.legend()
    plt.grid(True)
    plt.savefig('semi_distributed_simulation.png')
    print("Plot saved to semi_distributed_simulation.png")

if __name__ == "__main__":
    run_simulation()
