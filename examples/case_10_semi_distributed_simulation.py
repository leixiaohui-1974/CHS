import sys
import os
import matplotlib.pyplot as plt

from water_system_simulator.modeling.hydrology.sub_basin import SubBasin
from water_system_simulator.modeling.hydrology.semi_distributed import SemiDistributedHydrologyModel
from water_system_simulator.modeling.hydrology.runoff_models import XinanjiangModel
from water_system_simulator.modeling.hydrology.routing_models import MuskingumModel

def run_simulation():
    """
    This example demonstrates how to set up and run a simulation
    with the new vectorized SemiDistributedHydrologyModel.
    """
    # 1. Define configurations for a larger number of sub-basins
    num_basins = 100
    sub_basin_configs = []
    for i in range(num_basins):
        config = {
            "id": f"SB{i+1}",
            "area": 50.0 + i * 2,
            "coords": (i, i),
            "params": {
                "WM": 100 + i * 0.5, "B": 0.3, "IM": 0.05,
                "K": 12, "x": 0.2, "dt": 1,
                "initial_W": 50 + i * 0.2,
                "initial_inflow": 0.0,
                "initial_outflow": 0.0
            }
        }
        sub_basin_configs.append(config)

    # 2. Instantiate stateless runoff and routing strategies
    runoff_strategy = XinanjiangModel()
    routing_strategy = MuskingumModel()

    # 3. Create the main hydrological model
    # The model itself will handle the vectorized setup
    watershed_model = SemiDistributedHydrologyModel(
        sub_basins=sub_basin_configs,
        runoff_strategy=runoff_strategy,
        routing_strategy=routing_strategy
    )

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
