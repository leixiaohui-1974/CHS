import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import copy

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'water_system_sdk', 'src')))

from water_system_simulator.modeling.st_venant_model import StVenantModel
from water_system_simulator.modeling.storage_models import MuskingumChannelModel
from water_system_simulator.control.kalman_filter import KalmanFilter

def run_kf_tracking_simulation():
    """
    Demonstrates using a standard Kalman Filter to help a simple Muskingum model
    track the outflow of a complex St. Venant model.
    """
    print("--- Setting up Models ---")

    # 1. The "Real World": A St. Venant model for a simple channel
    nodes_config = [
        {'name': 'inflow', 'type': 'inflow', 'bed_elevation': 10, 'head': 15, 'inflow': 50, 'surface_area': 1000},
        {'name': 'outflow', 'type': 'level', 'bed_elevation': 9, 'head': 12, 'level': 12, 'surface_area': 1000}
    ]
    reaches_config = [
        {'name': 'r1', 'from_node': 'inflow', 'to_node': 'outflow', 'length': 5000, 'manning': 0.035, 'shape': 'trapezoidal', 'params': {'bottom_width': 25, 'side_slope': 2.0}}
    ]
    true_model = StVenantModel(copy.deepcopy(nodes_config), copy.deepcopy(reaches_config))

    # 2. The Simplified Prediction Model: A Muskingum model with imperfect parameters
    # The true 'K' for this reach is likely around 5000m / (1 m/s) ~= 5000s. Let's use imperfect params.
    dt = 60.0  # seconds
    muskingum_K = 4000.0 # Imperfect parameter
    muskingum_x = 0.15   # Imperfect parameter
    initial_flow = 50.0

    muskingum_model_open_loop = MuskingumChannelModel(
        K=muskingum_K, x=muskingum_x, dt=dt, initial_inflow=initial_flow, initial_outflow=initial_flow
    )
    # This model will be updated by the KF
    muskingum_model_kf = MuskingumChannelModel(
        K=muskingum_K, x=muskingum_x, dt=dt, initial_inflow=initial_flow, initial_outflow=initial_flow
    )

    print("--- Setting up Kalman Filter ---")

    # The state for the Muskingum model can be defined as [I_{t-1}, O_{t-1}]
    # The equation is O_t = C1*I_t + C2*I_{t-1} + C3*O_{t-1}
    # We want to estimate the state [I_{t-1}, O_{t-1}] to improve the O_t prediction.
    # However, I_{t-1} is just the previous input, which is known.
    # Let's define the state for the KF as just the outflow: x = [O]
    # The model is: O_t = C3*O_{t-1} + (C1*I_t + C2*I_{t-1})
    # This is a linear system where (C1*I_t + C2*I_{t-1}) is a control input.

    c1 = muskingum_model_kf.C1
    c2 = muskingum_model_kf.C2
    c3 = muskingum_model_kf.C3

    # State transition matrix F
    F = np.array([[c3]])

    # Observation matrix H (we directly observe the outflow)
    H = np.array([[1.0]])

    # Process noise covariance Q (uncertainty in the model)
    Q = np.array([[0.1**2]]) # std dev of 0.1 m3/s

    # Measurement noise covariance R (uncertainty in the St. Venant outflow observation)
    R = np.array([[0.5**2]]) # std dev of 0.5 m3/s

    # Initial state and covariance for KF
    x0 = np.array([initial_flow])
    P0 = np.array([[1.0]])

    kf = KalmanFilter(F=F, H=H, Q=Q, R=R, x0=x0, P0=P0)

    print("--- Running Simulation ---")
    num_steps = 200
    results = {
        'time': [],
        'true_outflow': [],
        'open_loop_outflow': [],
        'kf_outflow': [],
        'inflow': []
    }

    # To provide the necessary inputs to the Muskingum model
    inflow_history = [initial_flow]

    for i in range(num_steps):
        t = i * dt
        results['time'].append(t)

        # Vary the inflow to the true model to make it interesting
        current_inflow = 50 + 15 * np.sin(2 * np.pi * i / 150)
        true_model.network.get_node('inflow').inflow = current_inflow
        results['inflow'].append(current_inflow)

        # 1. Advance true model and get "real" outflow
        true_model.step(dt)
        true_outflow = true_model.get_state()['reaches']['r1']['discharge']
        results['true_outflow'].append(true_outflow)

        # 2. Advance open-loop Muskingum model
        muskingum_model_open_loop.input.inflow = current_inflow
        open_loop_outflow = muskingum_model_open_loop.step()
        results['open_loop_outflow'].append(open_loop_outflow)

        # 3. Create a noisy observation of the "real" outflow
        observation = true_outflow + np.random.normal(0, np.sqrt(R[0,0]))

        # 4. KF predict step
        # The control input u is (C1*I_t + C2*I_{t-1})
        # The predict equation is x_pred = F*x_est + B*u
        # Here, B is 1, and the KF class doesn't support control input.
        # We can augment the predict step slightly.
        inflow_tm1 = inflow_history[-1]
        kf_state_est = kf.get_state()

        # Predict based on previous state, then add the known input part
        predicted_state = F @ kf_state_est
        predicted_outflow = predicted_state[0] + c1 * current_inflow + c2 * inflow_tm1

        # Manually set the KF state after prediction
        kf.x[0] = predicted_outflow
        kf.P = F @ kf.P @ F.T + Q

        # 5. KF update step
        kf.update(np.array([observation]))

        # 6. Get corrected outflow and update the KF-driven Muskingum model
        corrected_outflow = kf.get_state()[0]
        results['kf_outflow'].append(corrected_outflow)

        # Update the Muskingum model's internal state for the next step
        muskingum_model_kf.state.outflow_prev = corrected_outflow
        muskingum_model_kf.input.inflow = current_inflow

        # Update inflow history
        inflow_history.append(current_inflow)

        if (i+1) % 20 == 0:
            print(f"Step {i+1}/{num_steps} complete.")

    # --- Plotting Results ---
    print("--- Plotting Results ---")
    plt.figure(figsize=(14, 8))
    plt.plot(results['time'], results['true_outflow'], 'b-', label='True Outflow (St. Venant)')
    plt.plot(results['time'], results['open_loop_outflow'], 'r--', label='Open-Loop Prediction (Muskingum)')
    plt.plot(results['time'], results['kf_outflow'], 'g-', lw=2, label='KF Corrected Prediction')
    plt.plot(results['time'], results['inflow'], 'k:', label='Inflow')

    plt.title('Kalman Filter Aiding a Simple Model to Track a Complex Model')
    plt.xlabel('Time (s)')
    plt.ylabel('Flow Rate (m^3/s)')
    plt.legend()
    plt.grid(True)
    plt.savefig('kf_dynamic_tracking.png')
    print("Saved tracking plot to kf_dynamic_tracking.png")
    plt.show()

if __name__ == "__main__":
    run_kf_tracking_simulation()
