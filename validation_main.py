import os
import json
import numpy as np
from water_system_simulator.hydrology.core import Basin, SubBasin, Reservoir
from water_system_simulator.control.parameter_assimilation import KFParameterEstimator
import matplotlib.pyplot as plt

def calculate_pseudo_observed_runoff(topology_data, timeseries_data, runoff_coeff=0.6):
    """
    Calculates a pseudo-observed runoff series based on total rainfall
    and a simple runoff coefficient.
    """
    num_steps = len(next(iter(timeseries_data["data"].values()))["precipitation_mm"])
    total_rainfall_volume_m3 = np.zeros(num_steps)

    for element in topology_data["elements"]:
        if element["type"] == "sub_basin":
            area_m2 = element["area_km2"] * 1_000_000
            precip_mm = np.array(timeseries_data["data"][element["id"]]["precipitation_mm"])
            precip_m = precip_mm / 1000
            total_rainfall_volume_m3 += precip_m * area_m2

    dt_seconds = timeseries_data["time_step_hours"] * 3600
    pseudo_observed_flow_m3s = (total_rainfall_volume_m3 / dt_seconds) * runoff_coeff
    return pseudo_observed_flow_m3s

def get_zone_c_precip_volume(topology_data, timeseries_data, time_step_t):
    """Calculates the total precipitation volume over Zone C for a given time step."""
    zone_c_precip_volume_m3 = 0
    zone_c_basins = ["C1", "C2", "C3"]
    for basin_id in zone_c_basins:
        element_data = next(el for el in topology_data["elements"] if el["id"] == basin_id)
        area_m2 = element_data["area_km2"] * 1_000_000
        precip_mm = timeseries_data["data"][basin_id]["precipitation_mm"][time_step_t]
        precip_m = precip_mm / 1000
        zone_c_precip_volume_m3 += precip_m * area_m2
    return zone_c_precip_volume_m3

def main():
    # --- Load Data ---
    base_path = "data/validation_case"
    with open(os.path.join(base_path, "topology.json"), 'r') as f:
        topology_data = json.load(f)
    with open(os.path.join(base_path, "parameters.json"), 'r') as f:
        params_data = json.load(f)
    with open(os.path.join(base_path, "timeseries.json"), 'r') as f:
        timeseries_data = json.load(f)

    # --- Run Baseline Simulation (No Assimilation) ---
    print("--- Running Baseline Simulation (for comparison) ---")
    baseline_basin = Basin(topology_data, params_data, timeseries_data)
    simulated_results = baseline_basin.run_simulation()
    outlet_id = "C3"
    simulated_hydrograph = simulated_results[outlet_id]
    print("Baseline simulation finished.")

    # --- Initialize for Assimilation Run ---
    print("--- Initializing for Assimilation Run ---")
    assimilation_basin = Basin(topology_data, params_data, timeseries_data)
    pseudo_observed_runoff = calculate_pseudo_observed_runoff(topology_data, timeseries_data)
    kf_estimator = KFParameterEstimator(initial_param_guess=0.4, process_noise=0.0001, measurement_noise=100)

    num_steps = len(pseudo_observed_runoff)
    assimilated_hydrograph = np.zeros(num_steps)
    parameter_history = np.zeros(num_steps)
    dt_hours = timeseries_data["time_step_hours"]

    # --- Run Step-by-Step Simulation with KF Assimilation ---
    print("--- Running Step-by-Step Simulation with KF Assimilation ---")
    for t in range(num_steps):
        # 1. Update parameter 'C' for Zone C sub-basins using the KF
        z_k = pseudo_observed_runoff[t]
        h_k = get_zone_c_precip_volume(topology_data, timeseries_data, t) / (dt_hours * 3600)
        updated_C = kf_estimator.run_step(z_k, h_k)
        parameter_history[t] = updated_C

        for basin_id in ["C1", "C2", "C3"]:
            assimilation_basin.elements[basin_id].runoff_model.params["C"] = updated_C

        # 2. Run a single time step of the simulation using the updated basin state
        current_outlet_flow = 0
        for element_id in assimilation_basin.simulation_order:
            element = assimilation_basin.elements[element_id]

            outflow = 0
            if isinstance(element, SubBasin):
                precip = timeseries_data["data"][element_id]["precipitation_mm"][t]
                evap = timeseries_data["data"][element_id]["evaporation_mm"][t]
                outflow = element.step(precip, evap, dt_hours)
            elif isinstance(element, Reservoir):
                outflow = element.step(dt_hours, t_step_debug=t)

            if element_id in assimilation_basin.reaches:
                reach = assimilation_basin.reaches[element_id]
                routed_outflow = reach.route(outflow)
                assimilation_basin.elements[reach.to_id].inflow += routed_outflow
                if element_id == outlet_id:
                    current_outlet_flow = routed_outflow
            elif element_id == outlet_id:
                current_outlet_flow = outflow

        assimilated_hydrograph[t] = current_outlet_flow

    print("Assimilation run finished.")

    # --- Plot Results ---
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12), sharex=True, gridspec_kw={'height_ratios': [3, 1]})

    ax1.plot(simulated_hydrograph, 'b-', label="Original Simulated Runoff (C=0.4)")
    ax1.plot(pseudo_observed_runoff, 'k--', label="Pseudo-Observed Runoff (Target, C=0.6)")
    ax1.plot(assimilated_hydrograph, 'r--', label="Assimilated Runoff (with KF)")
    ax1.set_title("Runoff Comparison")
    ax1.set_ylabel("Flow Rate (m³/s)")
    ax1.legend()
    ax1.grid(True)

    ax2.plot(parameter_history, 'g-', label="Runoff Coefficient 'C' for Zone C")
    ax2.axhline(y=0.6, color='k', linestyle='--', label="True' Parameter Value (0.6)")
    ax2.set_title("Kalman Filter Parameter Estimation")
    ax2.set_xlabel("Time Step (Days)")
    ax2.set_ylabel("Parameter Value")
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    output_filename = "validation_kf_assimilation.png"
    plt.savefig(output_filename)
    print(f"Assimilation comparison plot saved to {output_filename}")

if __name__ == "__main__":
    main()
