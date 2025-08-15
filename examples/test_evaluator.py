import sys
import os

# Adjust the Python path to include the source directory of the SDK
# The root of the repository.
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# The source directory containing the 'chs_sdk' package.
SRC_DIR = os.path.join(ROOT_DIR, 'water_system_sdk', 'src')
sys.path.insert(0, SRC_DIR)

# Also add the root directory to the path to allow finding the 'scenarios' module
sys.path.insert(0, ROOT_DIR)

from water_system_sdk.src.chs_sdk.workflows.utils.simulation_evaluator import evaluate_control_performance

def main():
    """
    A simple test script to run the evaluate_control_performance function.
    """
    print("Starting evaluation function test...")

    # 1. Define the system model to be controlled
    # This represents a water tank with a specific surface area.
    system_model = {
        'class': 'TankAgent',
        'params': {
            'area': 100.0,
            'initial_level': 10.0, # Start at the setpoint
            'max_level': 20.0
        }
    }

    # 2. Define the controller parameters to be evaluated
    # These are the PID gains.
    controller_config = {
        'Kp': 0.8,
        'Ki': 0.2,
        'Kd': 0.1
    }

    # 3. Choose the performance objective
    objective = 'ISE' # Integral of Squared Error

    print(f"System Model: {system_model}")
    print(f"Controller Config: {controller_config}")
    print(f"Objective: {objective}")

    try:
        # 4. Call the evaluation function
        cost = evaluate_control_performance(
            system_model=system_model,
            controller_config=controller_config,
            objective=objective
        )

        # 5. Print the result
        print("\n--- Test Result ---")
        print(f"Calculated Performance Cost ({objective}): {cost}")
        if isinstance(cost, float) and cost != float('inf'):
            print("Test PASSED: The function returned a valid float.")
        else:
            print("Test FAILED: The function returned an invalid value.")

    except Exception as e:
        print(f"\nAn error occurred during the test: {e}")
        import traceback
        traceback.print_exc()
        print("Test FAILED: An exception was raised.")


if __name__ == "__main__":
    main()
