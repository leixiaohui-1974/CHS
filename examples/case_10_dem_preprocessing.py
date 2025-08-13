import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# Add the SDK to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'water_system_sdk', 'src'))

from water_system_simulator.hydro_distributed.gistools import GISTools

def create_synthetic_dem_with_sink(rows=20, cols=20):
    """Creates a synthetic DEM with a slope and a sink."""
    x = np.arange(cols)
    y = np.arange(rows)
    xx, yy = np.meshgrid(x, y)

    # Create a base slope
    dem = 100 - (xx + yy * 2)

    # Add a sink in the middle
    sink_r, sink_c = rows // 2, cols // 2
    dem[sink_r-2:sink_r+2, sink_c-2:sink_c+2] = dem[sink_r, sink_c] - 10

    return dem.astype(np.float32)

def save_grid_as_image(grid, title, filename):
    """Saves a grid as a heatmap image."""
    plt.figure(figsize=(8, 6))
    plt.imshow(grid, cmap='viridis')
    plt.title(title)
    plt.colorbar(label='Value')
    plt.savefig(filename)
    plt.close()
    print(f"Saved {filename}")

def main():
    print("Starting DEM Preprocessing Verification Script")

    # --- 1. Setup ---
    # Ensure results directory exists
    results_dir = os.path.join(os.path.dirname(__file__), '..', 'results', 'dem_preprocessing')
    os.makedirs(results_dir, exist_ok=True)

    # --- 2. Create Synthetic DEM ---
    dem_original = create_synthetic_dem_with_sink()
    save_grid_as_image(dem_original, 'Original Synthetic DEM', os.path.join(results_dir, '01_original_dem.png'))

    # --- 3. Fill Sinks ---
    print("Running Fill Sinks...")
    dem_filled = GISTools.fill_sinks(dem_original)
    save_grid_as_image(dem_filled, 'DEM with Sinks Filled', os.path.join(results_dir, '02_filled_dem.png'))

    # --- 4. Calculate Flow Direction ---
    print("Calculating Flow Direction...")
    flow_dir = GISTools.flow_direction(dem_filled)
    save_grid_as_image(flow_dir, 'D8 Flow Direction', os.path.join(results_dir, '03_flow_direction.png'))

    # --- 5. Calculate Flow Accumulation ---
    print("Calculating Flow Accumulation...")
    flow_acc = GISTools.flow_accumulation(flow_dir)
    save_grid_as_image(flow_acc, 'Flow Accumulation', os.path.join(results_dir, '04_flow_accumulation.png'))

    print("\nVerification script finished.")
    print(f"Output images saved in: {results_dir}")

if __name__ == "__main__":
    main()
