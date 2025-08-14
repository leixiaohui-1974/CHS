import sys
import os
import pprint
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'water_system_sdk', 'src')))

from water_system_simulator.tools.identification_toolkit import generate_model_bank
from water_system_simulator.tools.simulation_helpers import run_piecewise_model, run_single_model
from water_system_simulator.utils.metrics import calculate_nse


def run_model_bank_generation():
    """
    Demonstrates the use of the generate_model_bank function and validates
    the resulting piecewise model against a single model.
    """
    print("--- Defining Base Configuration and Operating Space ---")

    # This configuration represents a simple river reach.
    base_config = {
        "components": {
            "StVenantModel": {
                "type": "StVenantModel",
                "properties": {
                    "nodes_data": [
                        {'name': 'UpstreamSource', 'type': 'inflow', 'bed_elevation': 10.0},
                        {'name': 'DownstreamSink', 'type': 'level', 'bed_elevation': 7.0}
                    ],
                    "reaches_data": [
                        {'name': 'r1', 'from_node': 'UpstreamSource', 'to_node': 'DownstreamSink', 'length': 15000, 'manning': 0.03, 'shape': 'trapezoidal', 'bottom_width': 20, 'side_slope': 2}
                    ],
                }
            }
        },
        "simulation_params": {"dt": 60},
        "execution_order": ["StVenantModel"]
    }

    # Define a wide operating space
    operating_space = [
        {'flow': 50 + i * 20, 'level': 12.0 + i * 0.1} for i in range(11)
    ]

    # Define the identification task
    task = {
        "model_type": "Muskingum",
        "input": "upstream_flow",
        "output": "downstream_flow"
    }

    # Create dummy validation data (a simple flood wave)
    time = np.arange(0, 86400, 3600)
    dt = time[1] - time[0]
    flow = 100 + 80 * np.sin(np.pi * time / 86400)**2
    validation_hydrograph = pd.DataFrame({'time': time, 'flow': flow})

    # Create dummy ground truth data (e.g., from a real St. Venant simulation)
    ground_truth_output = pd.DataFrame({'time': time, 'flow': flow * 0.9 + 10}) # Delayed and attenuated

    print(f"\n--- Generating Model Bank for Task: {task['model_type']} ---")

    try:
        model_bank = generate_model_bank(
            base_config=base_config,
            operating_space=operating_space,
            task=task,
            validation_hydrograph=validation_hydrograph,
            ground_truth_output=ground_truth_output,
            target_accuracy=0.85
        )

        print("\n--- Optimal Model Bank ---")
        pprint.pprint(model_bank)

        print("\n--- Validation Stage ---")
        inflow_series = validation_hydrograph['flow'].values
        ground_truth_series = ground_truth_output['flow'].values

        # 1. Run piecewise model
        piecewise_outflow = run_piecewise_model(inflow_series, model_bank, task['model_type'], dt)
        piecewise_nse = calculate_nse(piecewise_outflow, ground_truth_series)
        print(f"Piecewise Model NSE: {piecewise_nse:.4f}")

        # 2. Run single model with average parameters for comparison
        avg_params = {
            'K': np.mean([seg['parameters']['K'] for seg in model_bank]),
            'X': np.mean([seg['parameters']['X'] for seg in model_bank])
        }
        print(f"\nUsing average parameters for single model: {avg_params}")
        single_model_outflow = run_single_model(
            inflow_series,
            task['model_type'],
            avg_params,
            dt,
            initial_inflow=inflow_series[0],
            initial_outflow=inflow_series[0]
        )
        single_model_nse = calculate_nse(single_model_outflow, ground_truth_series)
        print(f"Single Model (Avg. Params) NSE: {single_model_nse:.4f}")

        # 3. Plot results
        plt.figure(figsize=(12, 7))
        plt.plot(time, ground_truth_series, 'k-', label='Ground Truth')
        plt.plot(time, piecewise_outflow, 'b--', label=f'Piecewise Model (NSE={piecewise_nse:.3f})')
        plt.plot(time, single_model_outflow, 'r:', label=f'Single Model (NSE={single_model_nse:.3f})')
        plt.plot(time, inflow_series, 'g-.', label='Inflow', alpha=0.6)
        plt.legend()
        plt.title('Piecewise vs. Single Model Validation')
        plt.xlabel('Time (s)')
        plt.ylabel('Flow (m^3/s)')
        plt.grid(True)
        plt.savefig('model_validation_comparison.png')
        print("\nSaved validation comparison plot to 'model_validation_comparison.png'")
        plt.close()


    except Exception as e:
        print(f"\nAn error occurred during model bank generation: {e}")

if __name__ == "__main__":
    run_model_bank_generation()
