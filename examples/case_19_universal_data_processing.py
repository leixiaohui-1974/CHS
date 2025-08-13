import sys
import os
import pandas as pd
import matplotlib.pyplot as plt

# Add the root directory to the Python path
# This allows us to import the SDK from this example script.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from water_system_sdk.src.water_system_simulator.simulation_manager import SimulationManager
from water_system_sdk.src.water_system_simulator.preprocessing.data_processor import (
    Pipeline,
    DataCleaner,
    InverseDistanceWeightingInterpolator,
)
from water_system_sdk.src.water_system_simulator.preprocessing.structures import RainGauge

def run_universal_data_processing_case():
    """
    Demonstrates the full workflow of:
    1. Loading raw external data (from a CSV).
    2. Using a processing pipeline to clean the data.
    3. Using a spatial interpolator to process the cleaned data.
    4. Feeding the final, processed data into a simulation model.
    """
    print("--- Running Universal Data Processing Example ---")

    # --- 1. Define Spatial Configuration ---
    # Define the locations of our rain gauges and our target (e.g., a sub-basin centroid)
    gauge_locations = {
        "gauge_1": (10, 20),
        "gauge_2": (50, 50),
        "gauge_3": (20, 60),
    }
    target_location = {"sub_basin_1": (30, 40)}

    # --- 2. Load Raw Data ---
    # Load raw data from the sample CSV file. It has missing values.
    raw_data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample_rainfall_data.csv')
    raw_df = pd.read_csv(raw_data_path, index_col='timestamp', parse_dates=True)
    print("\nRaw Data Head:")
    print(raw_df.head())

    # --- 3. Pre-simulation Data Processing ---
    # Create a processing pipeline. For now, it just cleans the data.
    # We use 'ffill' (forward fill) to handle missing data points.
    cleaning_pipeline = Pipeline(processors=[
        DataCleaner(strategy='ffill')
    ])
    cleaned_df = cleaning_pipeline.process(raw_df)
    print("\nCleaned Data Head:")
    print(cleaned_df.head())

    # Create RainGauge objects from the cleaned data.
    # The interpolator expects data in this format.
    rain_gauges = []
    for gauge_id, coords in gauge_locations.items():
        gauge_df = pd.DataFrame(cleaned_df[gauge_id]).rename(columns={gauge_id: 'precipitation'})
        rain_gauges.append(RainGauge(id=gauge_id, coords=coords, time_series=gauge_df))

    # Create and use the spatial interpolator.
    # This will generate a new time series for our target location.
    idw_interpolator = InverseDistanceWeightingInterpolator(
        rain_gauges=rain_gauges,
        target_locations=target_location
    )
    # The 'process' method takes the dataframe of all gauge data.
    interpolated_df = idw_interpolator.process(cleaned_df)
    print("\nInterpolated Data Head:")
    print(interpolated_df.head())

    # Extract the final time series for the simulation.
    inflow_pattern = interpolated_df['sub_basin_1'].tolist()

    # --- 4. Configure and Run Simulation ---
    # The processed data is now used as an input pattern for a standard agent.
    config = {
        "simulation_params": {
            "total_time": len(inflow_pattern) -1, # Simulate for the duration of our data
            "dt": 1.0
        },
        "components": {
            "inflow_agent": {
                "type": "RainfallAgent",
                "params": {
                    "rainfall_pattern": inflow_pattern
                }
            },
            "reservoir": {
                "type": "ReservoirModel",
                "params": {
                    "initial_level": 5.0,
                    "area": 1000, # m^2
                    "max_level": 20.0
                }
            }
        },
        "connections": [
            {"source": "inflow_agent.output", "target": "reservoir.input.inflow"},
        ],
        "execution_order": ["inflow_agent", "reservoir"],
        "logger_config": ["reservoir.state.level", "inflow_agent.output"]
    }

    manager = SimulationManager()
    results = manager.run(config)
    print("\nSimulation finished.")

    # --- 5. Plot Results for Verification ---
    plt.figure(figsize=(15, 12))

    # Plot raw vs. cleaned data for a gauge with missing values
    plt.subplot(3, 1, 1)
    raw_df['gauge_2'].plot(style='r--', label='Raw Gauge 2 Data', alpha=0.7)
    cleaned_df['gauge_2'].plot(style='g-', label='Cleaned Gauge 2 Data')
    plt.title('Data Cleaning Verification (Gauge 2)')
    plt.ylabel('Rainfall (mm/hr)')
    plt.legend()
    plt.grid(True)

    # Plot cleaned gauge data vs. the final interpolated inflow
    plt.subplot(3, 1, 2)
    cleaned_df['gauge_1'].plot(style='--', alpha=0.5, label='Cleaned Gauge 1')
    cleaned_df['gauge_2'].plot(style='--', alpha=0.5, label='Cleaned Gauge 2')
    cleaned_df['gauge_3'].plot(style='--', alpha=0.5, label='Cleaned Gauge 3')
    results['inflow_agent.output'].plot(style='b-', label='Interpolated Inflow for Target')
    plt.title('Spatial Interpolation Verification')
    plt.ylabel('Rainfall (mm/hr)')
    plt.legend()
    plt.grid(True)

    # Plot the final simulation output (reservoir level)
    plt.subplot(3, 1, 3)
    results['reservoir.state.level'].plot(label='Reservoir Water Level')
    plt.title('Reservoir Level Response to Processed Inflow')
    plt.xlabel('Time (steps)')
    plt.ylabel('Water Level (m)')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    output_path = os.path.join(os.path.dirname(__file__), '..', 'results', 'case_19_universal_data_processing.png')
    plt.savefig(output_path)
    print(f"\nVerification plot saved to {output_path}")

    return results

if __name__ == '__main__':
    run_universal_data_processing_case()
