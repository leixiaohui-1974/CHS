import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# Add the SDK to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'water_system_sdk', 'src'))

from water_system_simulator.hydro_distributed.distributed_hydrology_model import DistributedHydrologyModel

def create_v_shaped_watershed(rows=50, cols=30):
    """Creates a synthetic V-shaped watershed DEM."""
    x = np.arange(cols)
    y = np.arange(rows)
    xx, yy = np.meshgrid(x, y)
    center_col = cols // 2
    dem = 100 - np.abs(xx - center_col) * 0.5 - yy * 0.2
    return dem.astype(np.float32)

def main():
    print("Starting Full Distributed Model Simulation")

    # --- 1. Setup & Create Watershed Data ---
    results_dir = os.path.join(os.path.dirname(__file__), '..', 'results', 'full_model_simulation')
    os.makedirs(results_dir, exist_ok=True)

    dem = create_v_shaped_watershed()

    # Create heterogeneous curve number grid
    cn_grid = np.full(dem.shape, 75) # Default CN
    cn_grid[:, :dem.shape[1]//2] = 85 # Make one side less permeable

    # --- 2. Instantiate the Model ---
    print("Initializing the DistributedHydrologyModel...")
    model = DistributedHydrologyModel(dem=dem, curve_number_grid=cn_grid, channel_threshold=20)
    print("Model initialized successfully.")

    # --- 3. Define Rainfall Scenario ---
    timesteps = 24
    # Create a storm that moves across the basin
    rain_scenario = np.zeros((timesteps, dem.shape[0], dem.shape[1]))
    for t in range(12):
        intensity = np.sin(np.pi * t / 12) * 20 # Peak intensity of 20 mm/hr
        # Rain starts on the left side, then moves to the right
        rain_col_end = int((t / 12) * dem.shape[1])
        rain_scenario[t, :, :rain_col_end] = intensity

    # --- 4. Run Simulation ---
    print("Running simulation...")
    outlet_hydrograph = []
    for t in range(timesteps):
        rainfall_grid = rain_scenario[t, :, :]
        outlet_flow = model.step(rainfall_grid)
        outlet_hydrograph.append(outlet_flow)
        print(f"Time {t}: Rainfall input = {np.mean(rainfall_grid):.2f} mm, Outlet Flow = {outlet_flow:.2f}")

    # --- 5. Plot Results ---
    print("Plotting results...")

    # Plot 1: Hydrograph
    fig, ax1 = plt.subplots(figsize=(12, 7))
    total_rainfall_per_step = [np.mean(rain) for rain in rain_scenario]
    ax1.bar(range(timesteps), total_rainfall_per_step, color='blue', alpha=0.6, label='Avg Basin Rainfall')
    ax1.set_xlabel('Time (hours)')
    ax1.set_ylabel('Rainfall (mm/hr)', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')

    ax2 = ax1.twinx()
    ax2.plot(range(timesteps), outlet_hydrograph, 'r-o', label='Outlet Discharge')
    ax2.set_ylabel('Discharge (mm*cell_area/hr)', color='red')
    ax2.tick_params(axis='y', labelcolor='red')

    plt.title('Full Distributed Model Simulation')
    fig.tight_layout()
    plt.savefig(os.path.join(results_dir, '01_full_sim_hydrograph.png'))
    plt.close()

    # Plot 2: Final Soil Moisture
    final_state = model.get_state()
    soil_moisture_grid = final_state['soil_moisture']
    plt.figure(figsize=(8, 6))
    plt.imshow(soil_moisture_grid, cmap='YlGnBu')
    plt.title('Final Soil Moisture Distribution (mm)')
    plt.colorbar(label='Soil Moisture (mm)')
    plt.savefig(os.path.join(results_dir, '02_final_soil_moisture.png'))
    plt.close()

    print(f"\nSimulation finished. Plots saved to {results_dir}")

if __name__ == "__main__":
    main()
