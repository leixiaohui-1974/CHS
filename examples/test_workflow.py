import sys
import os
import pprint

# Adjust the Python path to include the source directory of the SDK
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_DIR = os.path.join(ROOT_DIR, 'water_system_sdk', 'src')
sys.path.insert(0, SRC_DIR)
sys.path.insert(0, ROOT_DIR)

from chs_sdk.workflows.control_tuning_workflow import ControlTuningWorkflow

def main():
    """
    A simple test script to run the ControlTuningWorkflow.
    """
    print("Starting ControlTuningWorkflow test...")

    # 1. Define the context for the workflow
    context = {
        'system_model': {
            'class': 'TankAgent',
            'params': {
                'area': 100.0,
                'initial_level': 10.0,
                'max_level': 20.0
            }
        },
        'optimization_objective': 'ISE',
        'parameter_bounds': [
            (0.1, 5.0),   # Kp bounds
            (0.01, 2.0),  # Ki bounds
            (0.0, 1.0)    # Kd bounds
        ],
        'initial_guess': [0.5, 0.1, 0.05] # Initial [Kp, Ki, Kd]
    }

    print("\nWorkflow Context:")
    pprint.pprint(context)

    try:
        # 2. Instantiate and run the workflow
        workflow = ControlTuningWorkflow()
        result = workflow.run(context)

        # 3. Print the results
        print("\n--- Workflow Result ---")
        print(f"Optimal Parameters: {result['optimal_params']}")
        print(f"Final Cost ({context['optimization_objective']}): {result['final_cost']}")

        # A simple check for success
        if isinstance(result['final_cost'], float) and 'Kp' in result['optimal_params']:
             print("\nTest PASSED: The workflow returned a valid result dictionary.")
        else:
             print("\nTest FAILED: The workflow returned an invalid result.")

    except Exception as e:
        print(f"\nAn error occurred during the workflow test: {e}")
        import traceback
        traceback.print_exc()
        print("Test FAILED: An exception was raised.")


if __name__ == "__main__":
    main()
