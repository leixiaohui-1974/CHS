import sys
import os
import pprint
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'water_system_sdk', 'src')))

from water_system_simulator.tools.identification_toolkit import generate_model_bank

def run_model_bank_generation():
    """
    Demonstrates the use of the generate_model_bank function to create
    an optimal piecewise model library for a given operating space.
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

        # (Optional) Visualize the parameter-condition map from dummy data
        # This part won't run now as the real param_map is internal to the function
        # but it shows the intent.
        flows = [p['flow'] for p in operating_space]
        # These are the dummy params generated inside the current toolkit
        dummy_Ks = [3600 - f * 10 for f in flows]
        dummy_Xs = [0.1 + f / 2000 for f in flows]

        fig, ax1 = plt.subplots(figsize=(10, 6))
        ax1.set_xlabel('Flow (m^3/s)')
        ax1.set_ylabel('Parameter K (s)', color='tab:blue')
        ax1.plot(flows, dummy_Ks, 'o-', color='tab:blue', label='K')
        ax1.tick_params(axis='y', labelcolor='tab:blue')

        ax2 = ax1.twinx()
        ax2.set_ylabel('Parameter X', color='tab:red')
        ax2.plot(flows, dummy_Xs, 's--', color='tab:red', label='X')
        ax2.tick_params(axis='y', labelcolor='tab:red')

        plt.title('Parameter-Condition Map (from Dummy Data)')
        fig.tight_layout()
        plt.savefig('parameter_map.png')
        print("\nSaved parameter map visualization to 'parameter_map.png'")
        plt.close()


    except Exception as e:
        print(f"\nAn error occurred during model bank generation: {e}")

if __name__ == "__main__":
    run_model_bank_generation()
