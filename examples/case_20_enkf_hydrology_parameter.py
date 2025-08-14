import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import copy

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'water_system_sdk', 'src')))

from water_system_simulator.modeling.hydrology.semi_distributed import SemiDistributedHydrologyModel
from water_system_simulator.modeling.hydrology.runoff_models import SCSRunoffModel
from water_system_simulator.modeling.hydrology.routing_models import MuskingumModel
from water_system_simulator.control.data_assimilation import EnsembleKalmanFilter

# --- EnKF Wrapper Functions ---
def state_transition_function_factory(model_config, dt, rainfall_ts):
    """
    Factory to create the state transition function for the EnKF.
    This function will simulate one step of the hydrological model.
    """
    def f(state_vector, t_index):
        # Unpack state and parameter
        I_prev, O_prev, cn = state_vector

        # Create a model instance for this specific step and ensemble member
        config = copy.deepcopy(model_config)
        config['sub_basins'][0]['params']['CN'] = cn # Set the CN from the state vector

        runoff_strategy = SCSRunoffModel()
        routing_strategy = MuskingumModel(states={"initial_inflow": I_prev, "initial_outflow": O_prev})

        model = SemiDistributedHydrologyModel(
            sub_basins=config['sub_basins'],
            runoff_strategy=runoff_strategy,
            routing_strategy=routing_strategy
        )

        # Run one step
        precipitation = rainfall_ts[t_index]
        model.step(dt=dt, t=t_index * dt, precipitation=precipitation)

        # Get the new state from the routing model
        new_routing_state = model.routing_strategy.get_state()
        new_inflow = new_routing_state['I_prev']
        new_outflow = new_routing_state['O_prev']

        # The parameter itself can evolve (e.g., random walk)
        # For this example, we assume it's constant during the predict step,
        # but process noise will be added to it later.
        new_cn = cn

        return np.array([new_inflow, new_outflow, new_cn])

    return f

def observation_function(state_vector):
    """
    The observation function h. It observes the outflow.
    """
    # The outflow is the second element of the state vector
    return np.array([state_vector[1]])

# --- Main Simulation ---
def run_enkf_parameter_estimation():
    """
    Main function to run the EnKF for hydrological parameter estimation.
    """
    print("--- Setting up Hydrological Models and Scenario ---")

    dt = 1.0 # hour
    num_steps = 150

    # Define a rainfall timeseries
    time = np.arange(num_steps)
    rainfall = np.zeros(num_steps)
    rainfall[20:40] = 15 + 10 * np.sin(np.pi * (time[20:40] - 20) / 20)
    rainfall[80:100] = 20 + 15 * np.sin(np.pi * (time[80:100] - 80) / 20)

    # Define the "true" time-varying CN parameter
    true_cn_ts = 75 + 10 * np.sin(2 * np.pi * time / 200)

    # Define the base model configuration
    model_config = {
        "sub_basins": [{
            "id": "sb1",
            "area": 50, # km2
            "coords": (0, 0), # Dummy coordinates
            "params": {
                "K": 12.0, # Muskingum K (hours)
                "x": 0.2,  # Muskingum x
                "CN": 75   # Initial CN
            }
        }]
    }

    # --- Run the "True" Model ---
    true_outflow_ts = []
    runoff_strategy_true = SCSRunoffModel()
    routing_strategy_true = MuskingumModel(states={"initial_inflow": 0.0, "initial_outflow": 0.0})
    true_model = SemiDistributedHydrologyModel(copy.deepcopy(model_config['sub_basins']), runoff_strategy_true, routing_strategy_true)

    for i in range(num_steps):
        true_model.sub_basins[0].params['CN'] = true_cn_ts[i]
        outflow = true_model.step(dt=dt, t=i*dt, precipitation=rainfall[i])
        true_outflow_ts.append(outflow)

    # --- Setup the EnKF ---
    print("--- Configuring the Ensemble Kalman Filter ---")

    n_ensemble = 50

    # Augmented state: [routing_inflow_prev, routing_outflow_prev, CN]
    state_size = 3

    # Initial state estimate (with a wrong CN)
    x0 = np.array([0.0, 0.0, 65.0])

    # Initial estimate covariance P0
    P0 = np.diag([0.1**2, 0.1**2, 5.0**2]) # High uncertainty on CN

    # Process noise Q (allows the parameter to evolve)
    Q = np.diag([0.01**2, 0.01**2, 0.5**2]) # Random walk for CN

    # Measurement noise R
    measurement_noise_std = 0.5 # m3/s
    R = np.diag([measurement_noise_std**2])

    # Create the state transition function
    f_enkf = state_transition_function_factory(model_config, dt, rainfall)

    # Create the EnKF instance
    enkf = EnsembleKalmanFilter(
        f=lambda x, t_index: f_enkf(x, t_index), # Wrap to match signature
        h=observation_function,
        Q=Q,
        R=R,
        x0=x0,
        P0=P0,
        n_ensemble=n_ensemble
    )

    # --- Run Assimilation Loop ---
    print("--- Running Data Assimilation ---")

    estimated_cn_ts = []
    estimated_outflow_ts = []

    for i in range(num_steps):
        # Predict step
        enkf.predict(t_index=i)

        # Create noisy observation
        observation = true_outflow_ts[i] + np.random.normal(0, measurement_noise_std)

        # Update step
        enkf.update(np.array([observation]))

        # Store results
        estimated_state = enkf.get_state()
        estimated_outflow_ts.append(estimated_state[1])
        estimated_cn_ts.append(estimated_state[2])

        if (i+1) % 20 == 0:
            print(f"Assimilation step {i+1}/{num_steps} complete.")

    # --- Plotting Results ---
    print("--- Plotting Results ---")

    fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

    # Plot 1: Parameter Tracking (CN)
    axes[0].plot(time, true_cn_ts, 'b-', label='True CN')
    axes[0].plot(time, estimated_cn_ts, 'g--', label='EnKF Estimated CN')
    axes[0].set_ylabel('SCS Curve Number (CN)')
    axes[0].set_title('EnKF Parameter Tracking for Hydrological Model')
    axes[0].legend()
    axes[0].grid(True)

    # Plot 2: Hydrograph Comparison
    axes[1].plot(time, true_outflow_ts, 'b-', label='True Outflow')
    axes[1].plot(time, estimated_outflow_ts, 'g--', label='EnKF Assimilated Outflow')
    # Add rainfall to secondary y-axis for context
    ax2 = axes[1].twinx()
    ax2.bar(time, rainfall, width=1.0, color='c', alpha=0.3, label='Rainfall')
    ax2.set_ylabel('Rainfall (mm/hr)')
    ax2.invert_yaxis()

    axes[1].set_xlabel('Time (hours)')
    axes[1].set_ylabel('Outflow (m^3/s)')
    lines, labels = axes[1].get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    axes[1].legend(lines + lines2, labels + labels2, loc='upper left')
    axes[1].grid(True)

    plt.tight_layout()
    plt.savefig('enkf_parameter_estimation.png')
    print("Saved results plot to enkf_parameter_estimation.png")
    plt.show()

if __name__ == "__main__":
    run_enkf_parameter_estimation()
