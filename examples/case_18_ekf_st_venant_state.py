import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import copy

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'water_system_sdk', 'src')))

from water_system_simulator.modeling.st_venant_model import StVenantModel
from water_system_simulator.control.data_assimilation import ExtendedKalmanFilter

# --- Helper Functions for State Conversion ---

def get_state_vector_map(model: StVenantModel):
    """Creates a map to convert between dict and vector states."""
    node_names = sorted([node.name for node in model.nodes])
    reach_names = sorted([reach.name for reach in model.reaches])
    # Assuming structures don't have a state to be estimated, but can be added
    return node_names, reach_names

def state_dict_to_array(state_dict: dict, node_names: list, reach_names: list) -> np.ndarray:
    """Converts a state dictionary to a flat numpy array."""
    node_heads = [state_dict['nodes'][name]['head'] for name in node_names]
    reach_discharges = [state_dict['reaches'][name]['discharge'] for name in reach_names]
    return np.array(node_heads + reach_discharges)

def state_array_to_dict(state_array: np.ndarray, node_names: list, reach_names: list) -> dict:
    """Converts a flat numpy array back to a state dictionary."""
    num_nodes = len(node_names)
    node_heads = state_array[:num_nodes]
    reach_discharges = state_array[num_nodes:]
    state_dict = {
        'nodes': {name: {'head': head} for name, head in zip(node_names, node_heads)},
        'reaches': {name: {'discharge': q} for name, q in zip(reach_names, reach_discharges)},
        'structures': {} # Assuming no structure state
    }
    return state_dict

# --- EKF Wrapper Functions ---

def model_step_wrapper(model: StVenantModel, dt: float, node_names: list, reach_names: list):
    """Wrapper for the StVenantModel step function to be used by the EKF."""
    def f(x: np.ndarray, *args, **kwargs) -> np.ndarray:
        state_dict = state_array_to_dict(x, node_names, reach_names)
        model.set_state(state_dict)
        model.step(dt)
        new_state_dict = model.get_state()
        return state_dict_to_array(new_state_dict, node_names, reach_names)
    return f

def get_jacobian_F(f, x, dt, epsilon=1e-6):
    """Computes the Jacobian of f by finite differences."""
    n = len(x)
    I = np.eye(n)
    J = np.zeros((n, n))
    f_x = f(x, dt)
    for i in range(n):
        x_plus_eps = x + epsilon * I[:, i]
        f_x_plus_eps = f(x_plus_eps, dt)
        J[:, i] = (f_x_plus_eps - f_x) / epsilon
    return J

def create_observation_func_and_jacobian(obs_node_indices: list, state_size: int):
    """Creates the observation function h and its Jacobian H."""
    H = np.zeros((len(obs_node_indices), state_size))
    for i, idx in enumerate(obs_node_indices):
        H[i, idx] = 1.0

    def h(x: np.ndarray) -> np.ndarray:
        return H @ x

    def H_jacobian(x: np.ndarray) -> np.ndarray:
        return H

    return h, H_jacobian

# --- Main Simulation ---

def run_ekf_venant_simulation():
    """
    Main function to run the EKF assimilation for the St. Venant model.
    """
    print("--- Setting up St. Venant Models (True, Open-Loop, EKF) ---")

    # A simple river: Inflow -> Reach1 -> Node2 -> Reach2 -> Node3 -> Reach3 -> Outflow
    nodes_config = [
        {'name': 'inflow', 'type': 'inflow', 'bed_elevation': 10, 'head': 15, 'inflow': 50},
        {'name': 'n2', 'type': 'junction', 'bed_elevation': 9},
        {'name': 'n3', 'type': 'junction', 'bed_elevation': 8},
        {'name': 'outflow', 'type': 'level', 'bed_elevation': 7, 'head': 10, 'level': 10}
    ]
    reaches_config = [
        {'name': 'r1', 'from_node': 'inflow', 'to_node': 'n2', 'length': 1000, 'manning': 0.03, 'shape': 'trapezoidal', 'params': {'bottom_width': 20, 'side_slope': 1.5}},
        {'name': 'r2', 'from_node': 'n2', 'to_node': 'n3', 'length': 1000, 'manning': 0.03, 'shape': 'trapezoidal', 'params': {'bottom_width': 20, 'side_slope': 1.5}},
        {'name': 'r3', 'from_node': 'n3', 'to_node': 'outflow', 'length': 1000, 'manning': 0.03, 'shape': 'trapezoidal', 'params': {'bottom_width': 20, 'side_slope': 1.5}}
    ]

    # Create three instances of the model
    true_model = StVenantModel(copy.deepcopy(nodes_config), copy.deepcopy(reaches_config))
    open_loop_model = StVenantModel(copy.deepcopy(nodes_config), copy.deepcopy(reaches_config))
    ekf_model = StVenantModel(copy.deepcopy(nodes_config), copy.deepcopy(reaches_config))

    # Get state vector mapping (consistent for all models)
    node_names, reach_names = get_state_vector_map(true_model)
    state_size = len(node_names) + len(reach_names)

    print(f"State vector size: {state_size}")
    print(f"Node mapping: {node_names}")
    print(f"Reach mapping: {reach_names}")

    # --- EKF Setup ---
    print("--- Configuring the Extended Kalman Filter ---")
    dt = 60.0  # Time step in seconds

    # State transition function
    f_ekf = model_step_wrapper(ekf_model, dt, node_names, reach_names)

    # Jacobian of f
    def F_jacobian_func(x, *args, **kwargs):
        # The model used for jacobian calculation needs to be a separate instance
        # to not mess up the state of the main ekf_model.
        temp_model = StVenantModel(copy.deepcopy(nodes_config), copy.deepcopy(reaches_config))
        f_temp = model_step_wrapper(temp_model, dt, node_names, reach_names)
        return get_jacobian_F(f_temp, x, dt)

    # Observation function (observe water level at n2 and n3)
    obs_node_names = ['n2', 'n3']
    obs_indices = [node_names.index(name) for name in obs_node_names]
    h_func, H_jacobian_func = create_observation_func_and_jacobian(obs_indices, state_size)

    # Noise matrices
    process_noise_std = 0.01
    Q = np.eye(state_size) * process_noise_std**2

    measurement_noise_std = 0.1 # 10cm noise on water level
    R = np.eye(len(obs_indices)) * measurement_noise_std**2

    # Initial state and covariance
    x0_array = state_dict_to_array(true_model.get_state(), node_names, reach_names)
    P0 = np.eye(state_size) * 0.1 # Initial uncertainty

    # Create the EKF instance
    ekf = ExtendedKalmanFilter(
        f=f_ekf,
        h=h_func,
        F_jacobian=F_jacobian_func,
        H_jacobian=H_jacobian_func,
        Q=Q,
        R=R,
        x0=x0_array,
        P0=P0
    )

    # --- Simulation Loop ---
    print("--- Running Simulation ---")
    num_steps = 100
    results = {
        'time': [],
        'true_state': [],
        'open_loop_state': [],
        'ekf_state': [],
        'observation': []
    }

    for i in range(num_steps):
        t = i * dt
        results['time'].append(t)

        # 1. Advance true model and get true state
        true_model.step(dt)
        true_state_arr = state_dict_to_array(true_model.get_state(), node_names, reach_names)
        results['true_state'].append(true_state_arr)

        # 2. Advance open-loop model
        open_loop_model.step(dt)
        open_loop_state_arr = state_dict_to_array(open_loop_model.get_state(), node_names, reach_names)
        results['open_loop_state'].append(open_loop_state_arr)

        # 3. Create a noisy observation from the true state
        true_observation = h_func(true_state_arr)
        observation = true_observation + np.random.normal(0, measurement_noise_std, len(obs_indices))
        results['observation'].append(observation)

        # 4. Run EKF predict and update
        ekf.predict(dt=dt) # predict is the step for the ekf_model
        ekf.update(observation)

        ekf_state_arr = ekf.get_state()
        results['ekf_state'].append(ekf_state_arr)

        if (i+1) % 10 == 0:
            print(f"Step {i+1}/{num_steps} complete.")

    # --- Plotting Results ---
    print("--- Plotting Results ---")

    # Convert results to numpy arrays
    for key in results:
        results[key] = np.array(results[key])

    # Plot water surface profiles at final time step
    plt.figure(figsize=(12, 7))
    num_nodes = len(node_names)
    node_dists = np.linspace(0, 3000, num_nodes)

    true_heads = results['true_state'][-1, :num_nodes]
    open_loop_heads = results['open_loop_state'][-1, :num_nodes]
    ekf_heads = results['ekf_state'][-1, :num_nodes]

    plt.plot(node_dists, true_heads, 'b-', label='True Water Surface')
    plt.plot(node_dists, open_loop_heads, 'r--', label='Open-Loop Prediction')
    plt.plot(node_dists, ekf_heads, 'g-+', label='EKF Assimilation')

    # Plot observation points
    obs_dists = [node_dists[i] for i in obs_indices]
    obs_heads = results['observation'][-1, :]
    plt.plot(obs_dists, obs_heads, 'ko', label='Noisy Observations')

    plt.title('Water Surface Profile Comparison at Final Time Step')
    plt.xlabel('Distance along river (m)')
    plt.ylabel('Water Head (m)')
    plt.legend()
    plt.grid(True)
    plt.savefig('ekf_water_surface_profile.png')
    print("Saved water surface profile plot to ekf_water_surface_profile.png")

    # Plot time series of water level at observed nodes
    fig, axes = plt.subplots(len(obs_indices), 1, figsize=(12, 10), sharex=True)
    for i, idx in enumerate(obs_indices):
        ax = axes[i]
        ax.plot(results['time'], results['true_state'][:, idx], 'b-', label='True Head')
        ax.plot(results['time'], results['open_loop_state'][:, idx], 'r--', label='Open-Loop Head')
        ax.plot(results['time'], results['ekf_state'][:, idx], 'g-+', label='EKF Head')
        ax.plot(results['time'], results['observation'][:, i], 'ko', markersize=3, label='Observation')
        ax.set_title(f'Water Head at Node {obs_node_names[i]}')
        ax.set_ylabel('Water Head (m)')
        ax.legend()
        ax.grid(True)

    axes[-1].set_xlabel('Time (s)')
    plt.tight_layout()
    plt.savefig('ekf_head_timeseries.png')
    print("Saved head time series plot to ekf_head_timeseries.png")
    plt.show()

if __name__ == "__main__":
    run_ekf_venant_simulation()
