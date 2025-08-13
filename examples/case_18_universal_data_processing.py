import sys
import os
import numpy as np

# Adjust path to add the 'src' directory, which contains the packages
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'water_system_sdk', 'src')))

from water_system_simulator.external_data.agents import CsvDataAgent
from water_system_simulator.modeling.hydrology.semi_distributed import SemiDistributedHydrologyModel
from water_system_simulator.modeling.st_venant_model import StVenantModel

# --- Mock Objects for Demonstration ---
# The actual strategies and sub-basins are complex. For this test, we only
# care about the data pipeline, so we create simple mock objects.

class MockRunoffModel:
    def calculate_runoff(self, rainfall, **kwargs):
        return rainfall * 0.8 # Assume 80% of rainfall becomes runoff
    def get_state(self): return {}

class MockRoutingModel:
    def route_flow(self, effective_rainfall, **kwargs):
        return effective_rainfall * 100 # A simple conversion to a flow value
    def get_state(self): return {}

class MockSubBasin:
    def __init__(self):
        self.params = {}

# --- Main Validation Script ---

def run_validation_case():
    """
    Validates the universal data processing pipeline architecture.
    """
    print("--- Setting up Universal Data Processing Validation Case ---")

    # 1. Initialize External Data Agents to read from CSV files
    print("\n[Step 1] Initializing ExternalDataAgents...")
    rainfall_agent = CsvDataAgent(id="rainfall_stations", file_path="data/rainfall_stations.csv")
    inflow_agent = CsvDataAgent(id="upstream_inflow", file_path="data/inflow.csv")
    print(f"  - {rainfall_agent.id} loaded: {not rainfall_agent.data.empty}")
    print(f"  - {inflow_agent.id} loaded: {not inflow_agent.data.empty}")
    assert not rainfall_agent.data.empty
    assert not inflow_agent.data.empty

    # 2. Configure and initialize the SemiDistributedHydrologyModel with its own pipeline
    print("\n[Step 2] Initializing SemiDistributedHydrologyModel with a data pipeline...")
    hydro_pipeline_config = [
        {
            "type": "InverseDistanceWeightingInterpolator",
            "params": {
                "id": "idw_interpolator",
                "station_locations": {"station1": (0, 0), "station2": (10, 5)},
                "target_location": (5, 2.5) # A point in the middle
            }
        },
        {
            "type": "UnitConverter",
            "params": {"id": "mm_to_m", "factor": 0.001}
        }
    ]

    watershed_model = SemiDistributedHydrologyModel(
        sub_basins=[MockSubBasin()],
        runoff_strategy=MockRunoffModel(),
        routing_strategy=MockRoutingModel(),
        data_pipeline=hydro_pipeline_config
    )
    print("  - Hydrology model created with pipeline:")
    for processor in watershed_model.data_pipeline:
        print(f"    - {processor.id} ({processor.__class__.__name__})")

    # 3. Configure and initialize the StVenantModel with a different pipeline
    print("\n[Step 3] Initializing StVenantModel with a data pipeline...")
    # Minimal config to instantiate the model
    nodes_data = [
        {'name': 'inflow_boundary', 'type': 'inflow', 'bed_elevation': 10, 'inflow': 0},
        {'name': 'outflow_boundary', 'type': 'level', 'bed_elevation': 5, 'level': 6}
    ]
    reaches_data = [
        {'name': 'r1', 'from_node': 'inflow_boundary', 'to_node': 'outflow_boundary',
         'length': 1000, 'manning': 0.03, 'shape': 'trapezoidal', 'params': {'bottom_width': 10}}
    ]

    hydrodynamic_pipeline_config = [
        {
            "type": "UnitConverter",
            "params": {"id": "cfs_to_cms", "factor": 0.0283168} # Cubic feet/s to cubic meters/s
        }
    ]

    river_model = StVenantModel(
        nodes_data=nodes_data,
        reaches_data=reaches_data,
        data_pipeline=hydrodynamic_pipeline_config
    )
    print("  - Hydrodynamic model created with pipeline:")
    for processor in river_model.data_pipeline:
        print(f"    - {processor.id} ({processor.__class__.__name__})")


    # 4. Run a simulation loop for a few time steps
    print("\n[Step 4] Running simulation loop and validating data processing...")
    dt = 1.0 # hours for hydrology, seconds for hydrodynamics
    for t in range(4):
        print(f"\n--- Time t = {t} ---")

        # --- Hydrology Model Step ---
        # a. Get raw data from the agent
        raw_rainfall_data = rainfall_agent.get_data(t)
        # b. Pass raw data to the model's input
        watershed_model.input = {"raw_rainfall": raw_rainfall_data}
        # c. The model's step method will now use the pipeline internally
        # We need to manually call the internal pipeline execution for this test
        processed_rainfall = watershed_model._execute_pipeline(raw_rainfall_data)

        print(f"  - Hydrology Input (raw): {raw_rainfall_data}")
        print(f"  - Hydrology Input (processed): {processed_rainfall:.6f} m")

        # Validation for hydrology pipeline at t=2
        if t == 2:
            # Manually calculate expected value
            s1_val, s2_val = 12, 14
            s1_loc, s2_loc = (0,0), (10,5)
            target_loc = (5, 2.5)
            dist1_sq = (5-0)**2 + (2.5-0)**2 # 25 + 6.25 = 31.25
            dist2_sq = (5-10)**2 + (2.5-5)**2 # 25 + 6.25 = 31.25
            w1 = 1 / dist1_sq**0.5
            w2 = 1 / dist2_sq**0.5
            # Since distances are equal, weights are equal, result is the average
            expected_interpolated = (s1_val + s2_val) / 2.0 # 13.0
            expected_converted = expected_interpolated * 0.001 # 0.013
            assert abs(processed_rainfall - expected_converted) < 1e-9, "Hydrology pipeline validation failed!"
            print("  - PASSED: Hydrology pipeline calculation is correct.")

        # --- Hydrodynamic Model Step ---
        # a. Get raw data
        raw_inflow_data = inflow_agent.get_data(t)
        # b. Pass raw data to model's input. The key 'raw_upstream_flow' and 'target_node'
        # are what the refactored StVenantModel expects.
        river_model.input = {
            'raw_upstream_flow': raw_inflow_data['flow'],
            'target_node': 'inflow_boundary'
        }
        # c. Execute step (which internally calls the pipeline via _update_boundaries)
        river_model.step(dt=dt*3600, t=t) # Convert dt to seconds

        processed_inflow = river_model.nodes_map['inflow_boundary'].inflow

        print(f"  - Hydrodynamic Input (raw): {raw_inflow_data['flow']} cfs")
        print(f"  - Hydrodynamic Input (processed): {processed_inflow:.4f} cms")

        # Validation for hydrodynamic pipeline at t=3
        if t == 3:
            expected_converted_inflow = 70 * 0.0283168 # 1.982176
            assert abs(processed_inflow - expected_converted_inflow) < 1e-6, "Hydrodynamic pipeline validation failed!"
            print("  - PASSED: Hydrodynamic pipeline calculation is correct.")

    print("\n--- Validation Complete ---")
    print("All checks passed. The universal data processing framework is working as expected.")


if __name__ == "__main__":
    run_validation_case()
