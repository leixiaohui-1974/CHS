import yaml
import pandas as pd
import matplotlib.pyplot as plt
from water_system_simulator.simulation_manager import SimulationManager
from water_system_simulator.config_parser import parse_topology

def run_and_plot_spatial_rainfall(config_path, output_image_path):
    """
    Runs the spatial rainfall simulation and generates comparison plots.
    """
    # Load configuration
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Run simulation
    manager = SimulationManager()
    results = manager.run(config)

    # --- Data Extraction for Plotting ---
    # Get the names of the sub-basins from the config
    sub_basin_ids = [sb['id'] for sb in config['components']['main_watershed']['params']['sub_basins']]

    # --- Data Extraction for Plotting ---
    # The 'main_watershed.input_rainfall' column in the results contains the full
    # interpolated rainfall DataFrame at each time step. Since it's generated
    # in preprocessing, it's the same in every row. We can just take the first one.
    interpolated_df = results['main_watershed.input_rainfall'].iloc[0]

    if not isinstance(interpolated_df, pd.DataFrame):
        raise TypeError("The logged 'main_watershed.input_rainfall' is not a DataFrame. Check the connection.")

    # The index of interpolated_df is timestamps, and columns are sub-basin IDs.
    # The simulation time is in the `results['time']` series.

    # Load original rain gauge data for comparison
    station_a = pd.read_csv('data/rain_gauges/station_A.csv', index_col='timestamp', parse_dates=True)
    station_b = pd.read_csv('data/rain_gauges/station_B.csv', index_col='timestamp', parse_dates=True)
    station_c = pd.read_csv('data/rain_gauges/station_C.csv', index_col='timestamp', parse_dates=True)

    # --- Plotting ---
    fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    fig.suptitle('Spatial Rainfall Interpolation Comparison', fontsize=16)

    # Plot 1: Interpolated Rainfall Time Series
    axes[0].set_title('Interpolated Rainfall at Sub-Basin Centroids')
    # Use the simulation time for the x-axis
    sim_time = results['time']
    for sb_id in sub_basin_ids:
        # Align the interpolated data with the simulation time
        rainfall_series = interpolated_df[sb_id].values[:len(sim_time)]
        axes[0].plot(sim_time, rainfall_series, label=f'Sub-Basin {sb_id}')

    # Also plot original station data for reference
    axes[0].plot(sim_time, station_a['precipitation'].values[:len(sim_time)], 'k--', label='Station A (Original)', alpha=0.7)
    axes[0].plot(sim_time, station_b['precipitation'].values[:len(sim_time)], 'r--', label='Station B (Original)', alpha=0.7)
    axes[0].plot(sim_time, station_c['precipitation'].values[:len(sim_time)], 'g--', label='Station C (Original)', alpha=0.7)

    axes[0].set_ylabel('Rainfall (mm)')
    axes[0].legend()
    axes[0].grid(True)

    # Plot 2: Scatter plot of rainfall field at a specific time step (e.g., t=4)
    axes[1].set_title('Spatial Rainfall Field at Time Step 4')

    # Get coordinates
    station_coords = {g['id']: g['coords'] for g in config['datasets']['rain_gauges']}
    sub_basin_coords = {sb['id']: sb['coords'] for sb in config['components']['main_watershed']['params']['sub_basins']}

    # Plot station locations and their rainfall at t=4
    time_step_to_plot = 4
    sta_a_val = station_a['precipitation'].iloc[time_step_to_plot]
    sta_b_val = station_b['precipitation'].iloc[time_step_to_plot]
    sta_c_val = station_c['precipitation'].iloc[time_step_to_plot]

    sc1 = axes[1].scatter(
        [c[0] for c in station_coords.values()],
        [c[1] for c in station_coords.values()],
        c=[sta_a_val, sta_b_val, sta_c_val],
        cmap='viridis', s=200, marker='^', edgecolors='k', label='Rain Gauges'
    )
    for name, coords in station_coords.items():
        axes[1].text(coords[0], coords[1] + 3, name)

    # Plot sub-basin locations and their interpolated rainfall at t=4
    sb_rainfall_t4 = interpolated_df.iloc[time_step_to_plot]
    sc2 = axes[1].scatter(
        [c[0] for c in sub_basin_coords.values()],
        [c[1] for c in sub_basin_coords.values()],
        c=[sb_rainfall_t4[sb_id] for sb_id in sub_basin_ids],
        cmap='viridis', s=150, marker='o', edgecolors='k', label='Sub-Basins'
    )
    for name, coords in sub_basin_coords.items():
        axes[1].text(coords[0], coords[1] + 3, name)

    axes[1].set_xlabel('X Coordinate')
    axes[1].set_ylabel('Y Coordinate')
    axes[1].grid(True)
    axes[1].legend()
    fig.colorbar(sc2, ax=axes[1], label='Rainfall (mm)')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(output_image_path)
    print(f"Validation plot saved to {output_image_path}")

if __name__ == "__main__":
    run_and_plot_spatial_rainfall(
        config_path='configs/case_spatial_rainfall.yml',
        output_image_path='spatial_rainfall_comparison.png'
    )
