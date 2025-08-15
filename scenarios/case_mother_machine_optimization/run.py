import sys
import os
import pprint

# Adjust the Python path to include the source directory of the SDK
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC_DIR = os.path.join(ROOT_DIR, 'water_system_sdk', 'src')
sys.path.insert(0, SRC_DIR)
sys.path.insert(0, ROOT_DIR)

from chs_sdk.factory.mother_machine import MotherMachine

def main():
    """
    This scenario demonstrates the end-to-end functionality of using the
    MotherMachine to automatically design an optimal PID controller.
    """
    print("--- Mother Machine: Optimal Controller Design Scenario ---")

    # 1. Instantiate the Mother Machine
    mother_machine = MotherMachine()

    # 2. Define the design problem
    design_params = {
        'system_model': {
            'class': 'TankAgent',
            'params': {
                'area': 120.0,      # A slightly different tank
                'initial_level': 10.0,
                'max_level': 20.0
            }
        },
        'optimization_objective': 'ISE',
        'parameter_bounds': [
            (0.1, 5.0),   # Kp
            (0.01, 2.0),  # Ki
            (0.0, 1.0)    # Kd
        ],
        'initial_guess': [0.5, 0.1, 0.05]
    }

    print("\nDesign Parameters:")
    pprint.pprint(design_params)

    try:
        # 3. Call the Mother Machine to design the controller
        print("\nRequesting optimal controller from Mother Machine...")
        optimal_pid_params = mother_machine.design_optimal_controller(**design_params)

        # 4. Display the results
        print("\n--- Design Complete ---")
        print("Mother Machine has designed the following PID controller:")
        print(f"  Kp: {optimal_pid_params.get('Kp'):.4f}")
        print(f"  Ki: {optimal_pid_params.get('Ki'):.4f}")
        print(f"  Kd: {optimal_pid_params.get('Kd'):.4f}")
        print("\nScenario PASSED: The Mother Machine successfully returned a controller design.")

    except Exception as e:
        print(f"\nAn error occurred during the scenario: {e}")
        import traceback
        traceback.print_exc()
        print("\nScenario FAILED.")


if __name__ == "__main__":
    main()
