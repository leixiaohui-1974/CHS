import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# Add the SDK to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'water_system_sdk', 'src'))

from water_system_simulator.hydro_distributed.gistools import GISTools
from water_system_simulator.hydro_distributed.routing import identify_river_network, HillslopeRouting, ChannelRouting

def create_v_shaped_watershed(rows=50, cols=30):
    """Creates a synthetic V-shaped watershed DEM."""
    x = np.arange(cols)
    y = np.arange(rows)
    xx, yy = np.meshgrid(x, y)

    center_col = cols // 2
    # Create two planes sloping towards the center
    dem = 100 - np.abs(xx - center_col) * 0.5 - yy * 0.2
    return dem.astype(np.float32)

def main():
    print("Starting Watershed Routing Verification Script")

    # --- 1. Setup & Create Watershed ---
    results_dir = os.path.join(os.path.dirname(__file__), '..', 'results', 'watershed_routing')
    os.makedirs(results_dir, exist_ok=True)

    dem = create_v_shaped_watershed()
    plt.imshow(dem); plt.title("V-Shaped DEM"); plt.savefig(os.path.join(results_dir, '01_v_shaped_dem.png')); plt.close()

    # --- 2. GIS Preprocessing ---
    print("Preprocessing DEM...")
    fdr = GISTools.flow_direction(dem)
    fac = GISTools.flow_accumulation(fdr)

    # --- 3. Identify Network and Route ---
    print("Identifying river network and calculating travel times...")
    channel_network = identify_river_network(fac, threshold=20)

    hillslope_router = HillslopeRouting(dem, fdr, cell_size=30)
    travel_times = hillslope_router.calculate_travel_times(channel_network)
    # Convert travel time from seconds to hours, assuming dt=1hr
    travel_times_hr = (travel_times / 3600.0).astype(int)

    # --- 4. Generate Runoff & Route ---
    print("Simulating runoff and routing...")
    # Create a single pulse of 10mm runoff everywhere
    runoff_pulse = np.full(dem.shape, 10.0)
    runoff_pulse[channel_network] = 0 # No runoff generated on channels themselves

    # Hillslope Routing: Create a time-area histogram (unit hydrograph)
    num_timesteps = 40
    lateral_inflow_hydrograph = np.zeros(num_timesteps)
    for t in range(num_timesteps):
        # Find all cells that will arrive at this timestep
        arriving_cells = (travel_times_hr == t)
        # Sum the runoff from these cells
        total_inflow = np.sum(runoff_pulse[arriving_cells])
        lateral_inflow_hydrograph[t] = total_inflow

    # Channel Routing
    # Parameters for a slow-moving channel
    channel_router = ChannelRouting(fdr, channel_network, k=3.0, x=0.2, dt=1.0) # K=3 hours, dt=1 hour
    outlet_r, outlet_c = np.unravel_index(np.argmax(fac), fac.shape)

    outlet_hydrograph = []
    for t in range(num_timesteps):
        # Create a grid of lateral inflows for this timestep
        # For simplicity, assume all lateral inflow enters the headwaters
        lateral_inflows_grid = np.zeros_like(dem, dtype=float)
        headwater_cells = (fac < 25) & channel_network
        if np.any(headwater_cells):
             # Distribute the total lateral inflow for this timestep among headwater cells
             lateral_inflows_grid[headwater_cells] = lateral_inflow_hydrograph[t] / np.sum(headwater_cells)

        channel_outflows = channel_router.route_flows(lateral_inflows_grid)
        outlet_flow = channel_outflows[outlet_r, outlet_c]
        outlet_hydrograph.append(outlet_flow)

    # --- 5. Plot Results ---
    plt.figure(figsize=(12, 7))
    plt.plot(lateral_inflow_hydrograph, 'b-o', label='Lateral Inflow to Channel (Hillslope Routed)')
    plt.plot(outlet_hydrograph, 'r-s', label='Outlet Flow (Channel Routed)')
    plt.title('Watershed Routing Simulation')
    plt.xlabel('Time (hours)')
    plt.ylabel('Flow Volume (mm * cell_area)')
    plt.legend()
    plt.grid(True)
    output_filename = os.path.join(results_dir, 'watershed_hydrograph.png')
    plt.savefig(output_filename)
    plt.close()

    print(f"\nSimulation finished. Plot saved to {output_filename}")

if __name__ == "__main__":
    main()
