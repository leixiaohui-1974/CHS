import os
import json
import copy
import logging
from hydrology.core import Basin
from hydrology.utils.file_parsers import (
    load_topology_from_json,
    load_timeseries_from_json,
)
import matplotlib.pyplot as plt

# It's good practice to have a logger instance per module.
logger = logging.getLogger(__name__)

def run_scenario(topology_data, base_params, timeseries_data, interception_enabled):
    """
    Runs a single simulation scenario with a given parameter set.
    This version passes data dictionaries directly to the Basin constructor.
    """
    # Create a deep copy of parameters to ensure isolated state for each run
    scenario_params = copy.deepcopy(base_params)

    # Modify the parameters for the specific scenario
    if "SubBasin1" in scenario_params:
        scenario_params["SubBasin1"]["human_activity_model"]["enabled"] = interception_enabled

    # Initialize and run the simulation for this scenario
    # Pass the data dictionaries directly
    basin = Basin(
        topology_data=topology_data,
        params_data=scenario_params,
        timeseries_data=timeseries_data,
    )
    results = basin.run_simulation()

    return results, basin.topology_data

def main():
    """
    Main function to run and compare two scenarios:
    1. Without human activity interception.
    2. With human activity interception.
    """
    # --- Basic logging setup ---
    # Since this is a standalone script, we can configure basic logging here.
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    # Load the data from files once at the beginning
    base_path = "data"
    topology_path = os.path.join(base_path, "topology.json")
    params_path = os.path.join(base_path, "parameters.json")
    timeseries_path = os.path.join(base_path, "timeseries.json")

    topology_data = load_topology_from_json(topology_path)
    timeseries_data = load_timeseries_from_json(timeseries_path)
    with open(params_path, 'r') as f:
        base_params = json.load(f)

    # --- Run Scenario 1: Interception Disabled ---
    logger.info("--- Running Scenario 1: Interception DISABLED ---")
    # Restore model to Xinanjiang for final test
    base_params["SubBasin1"]["runoff_model"] = "Xinanjiang"
    base_params["SubBasin2"]["runoff_model"] = "Xinanjiang"
    results_disabled, topology_data = run_scenario(
        topology_data, base_params, timeseries_data, interception_enabled=False
    )
    logger.info("Scenario 1 finished.")

    # --- Run Scenario 2: Interception Enabled ---
    logger.info("--- Running Scenario 2: Interception ENABLED ---")
    results_enabled, _ = run_scenario(
        topology_data, base_params, timeseries_data, interception_enabled=True
    )
    logger.info("Scenario 2 finished.")

    # --- Process and Display Results ---
    logger.info("--- Comparison Results ---")
    outlet_id = None
    for element in topology_data["elements"]:
        if element["downstream"] in topology_data["sinks"]:
            outlet_id = element["id"]
            break

    if outlet_id and outlet_id in results_disabled and outlet_id in results_enabled:
        hydrograph_disabled = results_disabled[outlet_id]
        hydrograph_enabled = results_enabled[outlet_id]

        logger.info(f"Outlet: {outlet_id}")
        logger.debug(f"Flow (Disabled): {[round(q, 2) for q in hydrograph_disabled]}")
        logger.debug(f"Flow (Enabled):  {[round(q, 2) for q in hydrograph_enabled]}")

        # Plot the results for comparison
        plt.figure(figsize=(12, 6))
        plt.plot(hydrograph_disabled, 'b-', marker='o', label=f"Interception Disabled (Xinanjiang)")
        plt.plot(hydrograph_enabled, 'r--', marker='x', label=f"Interception Enabled (Xinanjiang)")
        plt.title(f"Comparison of Hydrographs at Outlet '{outlet_id}'")
        plt.xlabel("Time Step (hours)")
        plt.ylabel("Flow Rate (m³/s)")
        plt.legend()
        plt.grid(True)

        output_filename = "hydrograph_comparison.png"
        plt.savefig(output_filename)
        logger.info(f"Comparison plot saved to {output_filename}")

    else:
        logger.warning("Could not determine a single outlet to plot.")

if __name__ == "__main__":
    main()
