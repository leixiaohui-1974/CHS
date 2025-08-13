import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# Add the SDK to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'water_system_sdk', 'src'))

from water_system_simulator.hydro_distributed.hydrological_unit import HydrologicalUnit

def run_single_cell_simulation():
    """
    Runs a simulation for a single hydrological unit and plots the results.
    """
    print("Starting single-cell runoff simulation...")

    # --- 1. Setup Hydrological Unit ---
    # CN=75 is for sandy clay loam, a common soil type.
    # We assume it's half-saturated to begin with.
    cell = HydrologicalUnit(curve_number=75, initial_soil_moisture_ratio=0.5)
    print(f"Cell created with CN={cell.cn}, Max Soil Storage={cell.soil_max_storage:.2f} mm")

    # --- 2. Create Synthetic Rainfall Event (Hyetograph) ---
    # A simple 12-hour storm event
    timesteps = 12
    rainfall_hyetograph = np.array([0, 5, 10, 25, 15, 10, 5, 2, 1, 0, 0, 0], dtype=float) # mm/hr
    time_axis = np.arange(timesteps) # hours

    # --- 3. Run Simulation ---
    runoff_hydrograph = []
    soil_moisture_over_time = []

    for i in range(timesteps):
        rainfall_mm = rainfall_hyetograph[i]
        # Assuming zero evapotranspiration during the storm for simplicity
        pot_et_mm = 0.0

        # Update the cell state and get the runoff
        runoff = cell.update_state(rainfall_mm, pot_et_mm)

        runoff_hydrograph.append(runoff)
        soil_moisture_over_time.append(cell.soil_moisture)

        print(f"Time {i} | Rain: {rainfall_mm:.1f} mm -> Runoff: {runoff:.2f} mm | Soil Moisture: {cell.soil_moisture:.2f} mm")

    # --- 4. Plot Results ---
    results_dir = os.path.join(os.path.dirname(__file__), '..', 'results', 'single_cell_runoff')
    os.makedirs(results_dir, exist_ok=True)
    output_filename = os.path.join(results_dir, 'runoff_hydrograph.png')

    fig, ax1 = plt.subplots(figsize=(12, 7))

    # Plot rainfall hyetograph on primary y-axis (ax1)
    ax1.set_xlabel('Time (hours)')
    ax1.set_ylabel('Rainfall (mm/hr)', color='blue')
    ax1.bar(time_axis, rainfall_hyetograph, color='blue', alpha=0.6, label='Rainfall')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.invert_yaxis() # To have bars point down like rain

    # Create a secondary y-axis (ax2) for the runoff hydrograph
    ax2 = ax1.twinx()
    ax2.set_ylabel('Runoff (mm/hr)', color='red')
    ax2.plot(time_axis, runoff_hydrograph, color='red', marker='o', linestyle='-', label='Runoff')
    ax2.tick_params(axis='y', labelcolor='red')

    plt.title('Single Cell Rainfall-Runoff Simulation (CN=75)')
    fig.tight_layout()
    plt.savefig(output_filename)
    plt.close()

    print(f"\nSimulation finished. Plot saved to {output_filename}")

if __name__ == "__main__":
    run_single_cell_simulation()
