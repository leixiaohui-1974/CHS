import sys
import os
import pandas as pd
import json

# Add the project root and the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'water_system_sdk', 'src')))


from chs_sdk.factory.mother_machine import MotherMachine

def run_mother_machine_e2e():
    """
    Runs an end-to-end test of the MotherMachine's cognitive and optimization capabilities.
    """
    print("--- Starting Mother Machine E2E Test ---")

    # 1. Load input data from CSV
    try:
        data_path = os.path.join(os.path.dirname(__file__), 'inflow_outflow_data.csv')
        input_data = pd.read_csv(data_path)
        print(f"Successfully loaded data from {data_path}")
    except FileNotFoundError:
        print(f"Error: Data file not found at {data_path}")
        return

    # 2. Instantiate MotherMachine
    mother_machine = MotherMachine()
    print("MotherMachine instantiated.")

    # 3. Step 1 (Cognition): Design Body Agent from data
    print("\n--- Step 1: Cognition - Designing Body Agent ---")
    try:
        body_agent_config = mother_machine.design_body_agent_from_data(
            agent_id="identified_river_reach",
            data=input_data,
            model_type="Muskingum",
            dt=1.0,
            initial_guess=[10.0, 0.2],
            bounds=([1e-9, 0], [100, 0.49])
        )
        print("Successfully designed Body Agent.")
        print("Body Agent Configuration:")
        print(json.dumps(body_agent_config, indent=2))
    except Exception as e:
        print(f"Error during Body Agent design: {e}")
        return

    # 4. Step 2 (Optimization): Design Optimal Controller from the identified model
    print("\n--- Step 2: Optimization - Designing Optimal Controller ---")
    try:
        # Define the arguments for the controller design
        optimization_objective = 'ISE'  # Integral of Squared Error
        parameter_bounds = [(0, 100), (0, 100), (0, 100)] # Bounds for Kp, Ki, Kd
        initial_guess = [1.0, 0.1, 0.01] # Initial guess for Kp, Ki, Kd

        optimal_pid_params = mother_machine.design_optimal_controller(
            system_model=body_agent_config,
            optimization_objective=optimization_objective,
            parameter_bounds=parameter_bounds,
            initial_guess=initial_guess
        )
        print("Successfully designed Optimal Controller.")
        print("\n--- Final Result: Optimal PID Parameters ---")
        print(optimal_pid_params)

    except Exception as e:
        print(f"Error during Optimal Controller design: {e}")
        return

    print("\n--- Mother Machine E2E Test Completed Successfully ---")

if __name__ == "__main__":
    run_mother_machine_e2e()
