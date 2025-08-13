import sys
import os
import pprint

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'water_system_sdk', 'src')))

# Import the high-level model
from water_system_simulator.modeling.st_venant_model import StVenantModel

def run_integrated_weir_simulation():
    """
    Runs a weir simulation using the high-level StVenantModel.
    This demonstrates the final integration into the SDK.
    """
    print("--- Defining Network via Configuration Dictionaries ---")

    # Define nodes as a list of dicts
    nodes_config = [
        {
            'name': 'UpstreamSource',
            'type': 'inflow',
            'inflow': 10.0,
            'bed_elevation': 5.0,
            'head': 10.5,
            'surface_area': 5000
        },
        {
            'name': 'DownstreamSink',
            'type': 'level',
            'level': 8.0,
            'bed_elevation': 4.5,
            'head': 8.0,
            'surface_area': 5000
        }
    ]

    # No reaches in this simple model
    reaches_config = []

    # Define structures (the weir) as a list of dicts
    structures_config = [
        {
            'name': 'MainWeir',
            'type': 'weir',
            'from_node': 'UpstreamSource',
            'to_node': 'DownstreamSink',
            'crest_elevation': 11.0,
            'weir_coefficient': 1.7,
            'crest_width': 15.0,
            'discharge': 0.0
        }
    ]

    # Define solver parameters
    solver_config = {
        'tolerance': 1e-4,
        'max_iterations': 20,
        'relaxation_factor': 0.5
    }

    print("--- Initializing StVenantModel ---")
    model = StVenantModel(
        nodes_data=nodes_config,
        reaches_data=reaches_config,
        structures_data=structures_config,
        solver_params=solver_config
    )

    print("Model initialized. Initial state:")
    pprint.pprint(model.get_state())
    print("-" * 30)

    # --- Simulation Loop ---
    dt = 2.0
    num_steps = 800
    print(f"Running simulation for {num_steps} steps with dt={dt}s...")

    for step in range(num_steps):
        success = model.step(dt)
        if not success:
            print(f"Solver failed at step {step + 1}. Halting simulation.")
            break

        if (step + 1) % 100 == 0:
            print(f"State at step {step + 1}:")
            pprint.pprint(model.output)

    print("-" * 30)
    print("Final state:")
    final_state = model.get_state()
    pprint.pprint(final_state)

    # --- Verification ---
    print("\n--- Verification ---")
    final_flow = final_state['structures']['MainWeir']['discharge']
    if final_flow > 9.9 and final_flow < 10.1:
        print(f"PASSED: Final weir discharge ({final_flow:.2f}) is approximately equal to inflow (10.0).")
    else:
        print(f"FAILED: Final weir discharge ({final_flow:.2f}) is not close to inflow (10.0).")

if __name__ == "__main__":
    run_integrated_weir_simulation()
