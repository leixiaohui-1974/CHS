import numpy as np
import sys
import os

# Add the src directory to the Python path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'water_system_sdk', 'src')))

try:
    from water_system_simulator.preprocessing.delineation import WatershedDelineator
    from water_system_simulator.preprocessing.parameterization import ParameterExtractor
except ImportError as e:
    print("Failed to import preprocessing modules.")
    print("Please ensure you are running this script from the repository root.")
    sys.exit(1)


def create_dummy_gis_data():
    """
    Creates simple, synthetic GIS data. This DEM is idealized and does not require
    sink filling, as it has proper slopes and a clear outlet on the border.
    """
    print("--- Creating Dummy GIS Data ---")
    dem = np.ones((50, 50), dtype=np.float32) * 100

    main_channel_slope = np.linspace(85, 76, 35)
    for i in range(10, 45):
        dem[i, 24:26] = main_channel_slope[i-10]

    for i in range(10, 45):
        dem[i, 10:24] = dem[i, 24] + np.linspace(10, 0.1, 14)
        dem[i, 26:40] = dem[i, 25] + np.linspace(0.1, 10, 14)

    trib_channel_slope = np.linspace(90, dem[20, 24], 15)
    dem[20, 10:25] = trib_channel_slope

    dem[49, 24] = 70
    print("DEM with proper slopes and a border outlet created.")

    land_use = np.full((50, 50), 10, dtype=np.int32)
    land_use[15:35, 15:23] = 20; land_use[15:35, 27:35] = 30; land_use[35:45, 20:30] = 40
    soil_type = np.full((50, 50), 2, dtype=np.int32)
    soil_type[25:40, 10:40] = 3; soil_type[38:45, 22:28] = 4
    print("Land Use and Soil Type grids created.")
    print("Dummy data creation complete.\n")
    return dem, land_use, soil_type

def print_results(zones):
    """Prints the results of the preprocessing in a readable format."""
    print("\n\n#########################################")
    print("#      AUTOMATED PREPROCESSING REPORT     #")
    print("#########################################")
    for zone in zones:
        print(f"\n========================================")
        print(f" PARAMETER ZONE: {zone.id}")
        print(f"========================================")
        print(f"  - Observation Point (row, col): {zone.observation_point}")
        print(f"  - Total Cells in Zone Mask: {np.sum(zone.mask)}")
        print(f"  - Number of Sub-basins Delineated: {len(zone.sub_basins)}")
        for sub_basin in zone.sub_basins:
            print(f"\n  ------------------------------------")
            print(f"  SUB-BASIN: {sub_basin.id}")
            print(f"  ------------------------------------")
            print(f"    Physical Parameters:")
            for key, val in sub_basin.physical_parameters.items():
                print(f"      - {key+':':<20} {val:.4f}")
            print(f"    Generated Model Parameters:")
            for key, val in sub_basin.model_parameters.items():
                print(f"      - {key+':':<20} {val:.4f}")

def main():
    """Main function to run the automated model setup case."""
    dem, land_use, soil_type = create_dummy_gis_data()
    cell_size_m = 30.0
    outlet_points = [(20, 24), (44, 24)]
    print(f"--- Delineation Setup ---")
    print(f"Outlets defined at (row, col): {outlet_points}")

    print("\n--- Running Watershed Delineator ---")
    delineator = WatershedDelineator(dem=dem)
    # Bypass sink filling for this idealized DEM
    zones = delineator.delineate_parameter_zones(
        outlet_points=outlet_points,
        perform_sink_fill=False
    )

    stream_threshold = 20
    zones_with_subbasins = delineator.delineate_sub_basins(zones=zones, stream_threshold=stream_threshold)

    print("\n--- Running Parameter Extractor ---")
    extractor = ParameterExtractor(
        dem=delineator.filled_dem,
        land_use=land_use,
        soil_type=soil_type,
        cell_size_m=cell_size_m
    )
    final_zones = extractor.extract_all_parameters(zones=zones_with_subbasins)

    print_results(final_zones)

if __name__ == "__main__":
    main()
