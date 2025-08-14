import sys
import os
import pprint

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'water_system_sdk', 'src')))

from water_system_simulator.tools.identification_toolkit import identify_at_point

def run_single_point_identification():
    """
    Demonstrates the use of the identify_at_point function to identify
    simplified model parameters for a StVenantModel at a specific operating point.
    """
    print("--- Defining Base Configuration for a St. Venant Model ---")

    # This configuration represents a simple river reach.
    base_config = {
        "components": {
            "StVenantModel": {
                "type": "StVenantModel",
                "properties": {
                    "nodes_data": [
                        {'name': 'UpstreamSource', 'type': 'inflow', 'bed_elevation': 10.0, 'inflow': 100.0},
                        {'name': 'n1', 'type': 'junction', 'bed_elevation': 9.0},
                        {'name': 'n2', 'type': 'junction', 'bed_elevation': 8.0},
                        {'name': 'DownstreamSink', 'type': 'level', 'bed_elevation': 7.0, 'level': 12.0}
                    ],
                    "reaches_data": [
                        {'name': 'r1', 'from_node': 'UpstreamSource', 'to_node': 'n1', 'length': 5000, 'manning': 0.03, 'shape': 'trapezoidal', 'bottom_width': 20, 'side_slope': 2},
                        {'name': 'r2', 'from_node': 'n1', 'to_node': 'n2', 'length': 5000, 'manning': 0.03, 'shape': 'trapezoidal', 'bottom_width': 20, 'side_slope': 2},
                        {'name': 'r3', 'from_node': 'n2', 'to_node': 'DownstreamSink', 'length': 5000, 'manning': 0.03, 'shape': 'trapezoidal', 'bottom_width': 20, 'side_slope': 2},
                    ],
                    "structures_data": [],
                    "solver_params": {'tolerance': 1e-4, 'max_iterations': 20}
                }
            }
        },
        "simulation_params": {
            "total_time": 7200,
            "dt": 60,
        },
        "execution_order": ["StVenantModel"],
        "logger_config": [] # Will be set by the identification tool
    }

    print("--- Defining Operating Point and Identification Tasks ---")

    # Define the steady-state operating point to be identified
    operating_point = {
        'upstream_flow': 200.0,
        'downstream_level': 13.5
    }

    # Define the list of identification tasks
    identification_tasks = [
        {
            "model_type": "Muskingum",
            "input": "upstream_flow",
            "output": "downstream_flow"
        },
        {
            "model_type": "IntegralDelay",
            "input": "upstream_flow",
            "output": "downstream_level"
        },
        {
            "model_type": "IntegralDelay",
            "input": "downstream_level",
            "output": "upstream_level"
        },
        {
            "model_type": "IntegralDelay",
            "input": "upstream_flow",
            "output": "upstream_level"
        },
        {
            "model_type": "IntegralDelay",
            "input": "downstream_level",
            "output": "downstream_flow"
        }
    ]

    print(f"\n--- Running Identification at Operating Point: Q={operating_point['upstream_flow']}, H={operating_point['downstream_level']} ---")

    # Because the toolkit is not fully integrated yet, we expect this to use the dummy data.
    # The goal here is to test the structure and the API call.
    try:
        # The operating point needs to be mapped to the config structure
        op_point_for_tool = {
            "StVenantModel.properties.nodes_data.0.inflow": operating_point['upstream_flow'],
            "StVenantModel.properties.nodes_data.3.level": operating_point['downstream_level']
        }

        identified_params = identify_at_point(
            base_config=base_config,
            operating_point=op_point_for_tool,
            identification_tasks=identification_tasks
        )

        print("\n--- Identification Results ---")
        pprint.pprint(identified_params)

    except Exception as e:
        print(f"\nAn error occurred during identification: {e}")
        print("This might be expected as the toolkit is still under development.")


if __name__ == "__main__":
    run_single_point_identification()
