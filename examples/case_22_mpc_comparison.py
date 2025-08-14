import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import copy
import sys
import os
import collections

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'water_system_sdk', 'src')))

from water_system_simulator.modeling.integral_plus_delay_model import IntegralPlusDelayModel
from water_system_simulator.control.mpc_controller import MPCController
from water_system_simulator.control.gs_mpc_controller import GainScheduledMPCController
from water_system_simulator.control.kalman_adaptive_mpc_controller import KalmanAdaptiveMPCController
from water_system_simulator.control.data_assimilation import ExtendedKalmanFilter
from water_system_simulator.modeling.base_model import BaseModel


# --- A Custom Agent for Parameter Estimation using an EKF ---
class ParameterEKFWrapper(BaseModel):
    """
    A wrapper to use the ExtendedKalmanFilter for parameter estimation of an
    IntegralPlusDelayModel (K, T).
    """
    def __init__(self, dt, initial_params, P0, Q, R):
        super().__init__()
        self.dt = dt
        # Increase history size to be safe
        self.state_history = collections.deque(maxlen=int(initial_params['T'] / dt) * 2)
        self.input_history = collections.deque(maxlen=int(initial_params['T'] / dt) * 2)

        x0 = np.array([initial_params['K'], initial_params['T']])

        def f(x, *args, **kwargs): return x
        def F_jacobian(x, *args, **kwargs): return np.eye(2)

        def h(x):
            K, T = x
            delay_steps = int(round(T / self.dt))
            if len(self.input_history) > delay_steps:
                y_prev = self.state_history[-1]
                u_delayed = self.input_history[-(delay_steps + 1)]
                return y_prev + K * u_delayed * self.dt
            return self.state_history[-1] if self.state_history else 0.0

        def H_jacobian(x):
            K, T = x
            delay_steps = int(round(T / self.dt))
            if len(self.input_history) > delay_steps + 1:
                u_delayed = self.input_history[-(delay_steps + 1)]
                u_delayed_prev = self.input_history[-(delay_steps + 2)]
                dh_dK = u_delayed * self.dt
                dh_dT = -K * (u_delayed - u_delayed_prev)
                return np.array([[dh_dK, dh_dT]])
            return np.array([[0.0, 0.0]])

        self.ekf = ExtendedKalmanFilter(f, h, F_jacobian, H_jacobian, Q, R, x0, P0)
        self.estimated_params = {'K': x0[0], 'T': x0[1]}

    def step(self, plant_input, plant_output):
        if plant_input is None or plant_output is None: return self.estimated_params
        self.input_history.append(plant_input)
        self.state_history.append(plant_output)
        if len(self.state_history) < 2: return self.estimated_params
        self.ekf.predict()
        self.ekf.update(np.array([plant_output]))
        est_K, est_T = self.ekf.get_state()
        self.estimated_params['K'] = np.clip(est_K, 0.001, 0.02)
        self.estimated_params['T'] = np.clip(est_T, 1000, 3000)
        return self.estimated_params

    def get_state(self): return self.estimated_params

# --- Manual Simulation Runner ---
def run_manual_simulation(plant, controller, disturbance_ts, true_K_ts, true_T_ts, num_steps, dt, estimator=None):
    history = []
    plant_output = plant.get_state()['output']
    control_action = 0.0

    for i in range(num_steps):
        # Update plant's true parameters
        plant.K = true_K_ts[i]
        plant.T = true_T_ts[i]
        plant.delay_steps = int(round(plant.T / dt))

        disturbance = disturbance_ts[i]

        # Controller step
        controller_args = {
            'current_state': plant_output,
            'disturbance_forecast': np.full(controller.P, disturbance)
        }
        if isinstance(controller, GainScheduledMPCController):
            controller_args['scheduling_variable'] = disturbance
        elif isinstance(controller, KalmanAdaptiveMPCController) and estimator:
             # Estimator step
            total_plant_inflow = disturbance + control_action
            estimated_params = estimator.step(total_plant_inflow, plant_output)
            controller_args['updated_model_params'] = estimated_params

        control_action = controller.step(**controller_args)

        # Plant step
        plant.input.inflow = disturbance
        plant.input.control_inflow = control_action
        plant.step()
        plant_output = plant.get_state()['output']

        # Log data
        log_entry = {
            'time': i * dt,
            'plant_output': plant_output,
            'control_action': control_action,
            'disturbance': disturbance,
            'true_K': plant.K,
            'true_T': plant.T
        }
        if estimator:
            log_entry.update({f'est_{k}': v for k, v in estimator.get_state().items()})
        history.append(log_entry)

    return pd.DataFrame(history)

def run_mpc_comparison():
    print("--- Setting up MPC Comparison Scenario ---")
    dt, sim_duration = 100.0, 100000.0
    num_steps = int(sim_duration / dt)
    set_point = 10.0

    time_vector = np.arange(0, sim_duration, dt)
    true_initial_K, true_initial_T = 0.008, 1800.0
    true_K_ts = true_initial_K * (1 + 0.25 * np.sin(2 * np.pi * time_vector / sim_duration))
    true_T_ts = true_initial_T * (1 - 0.25 * np.sin(2 * np.pi * time_vector / (sim_duration / 2)))

    disturbance_ts = np.full(num_steps, 50.0)
    disturbance_ts[int(num_steps / 2):] = 80.0

    P, M = 30, 5
    avg_K, avg_T = np.mean(true_K_ts), np.mean(true_T_ts)

    # --- Run Scenarios ---
    results = {}
    for scenario in ["StandardMPC", "GainScheduledMPC", "KalmanAdaptiveMPC"]:
        print(f"--- Running Scenario: {scenario} ---")
        plant = IntegralPlusDelayModel(K=true_initial_K, T=true_initial_T, dt=dt, initial_value=set_point)
        plant.input_buffer = collections.deque([50.0] * int(plant.T / dt), maxlen=int(plant.T / dt))

        controller = None
        estimator = None
        if scenario == "StandardMPC":
            controller = MPCController(prediction_model=IntegralPlusDelayModel(K=avg_K, T=avg_T, dt=dt),
                                     prediction_horizon=P, control_horizon=M, set_point=set_point,
                                     u_min=0, u_max=100, q_weight=1.0, r_weight=0.05)
        elif scenario == "GainScheduledMPC":
            model_bank = [{"threshold": 60, "K": 0.007, "T": 2200}, {"threshold": 90, "K": 0.009, "T": 1600}]
            controller = GainScheduledMPCController(model_bank=model_bank, initial_model_params={'K': avg_K, 'T': avg_T}, dt=dt,
                                                  prediction_horizon=P, control_horizon=M, set_point=set_point,
                                                  u_min=0, u_max=100, q_weight=1.0, r_weight=0.05)
        elif scenario == "KalmanAdaptiveMPC":
            initial_params_guess = {'K': 0.006, 'T': 2300.0}
            controller = KalmanAdaptiveMPCController(initial_model_params=initial_params_guess, dt=dt,
                                                     prediction_horizon=P, control_horizon=M, set_point=set_point,
                                                     u_min=0, u_max=100, q_weight=1.0, r_weight=0.05)
            P0 = np.diag([0.005**2, 500**2])
            Q = np.diag([(0.008*0.01)**2, (1800*0.01)**2])
            R = np.diag([0.01**2])
            estimator = ParameterEKFWrapper(dt, initial_params_guess, P0, Q, R)

        results[scenario] = run_manual_simulation(plant, controller, disturbance_ts, true_K_ts, true_T_ts, num_steps, dt, estimator)

    # --- Plotting Results ---
    print("--- Plotting Results ---")
    fig, axes = plt.subplots(2, 1, figsize=(15, 12), sharex=True)

    axes[0].axhline(y=set_point, color='k', linestyle='--', label='Setpoint')
    axes[0].plot(results["StandardMPC"]['time'], results["StandardMPC"]['plant_output'], label='Standard MPC')
    axes[0].plot(results["GainScheduledMPC"]['time'], results["GainScheduledMPC"]['plant_output'], label='Gain-Scheduled MPC')
    axes[0].plot(results["KalmanAdaptiveMPC"]['time'], results["KalmanAdaptiveMPC"]['plant_output'], label='Kalman-Adaptive MPC', linewidth=2)
    axes[0].set_ylabel('Water Level (m)')
    axes[0].set_title('MPC Controller Performance Comparison')
    axes[0].legend()
    axes[0].grid(True)

    ax0_twin = axes[0].twinx()
    ax0_twin.plot(results["StandardMPC"]['time'], results["StandardMPC"]['disturbance'], 'r--', alpha=0.5, label='Disturbance Inflow')
    ax0_twin.set_ylabel('Disturbance (m³/s)')
    ax0_twin.legend(loc='lower right')

    kalman_results = results["KalmanAdaptiveMPC"]
    axes[1].plot(kalman_results['time'], kalman_results['true_K'], 'b-', label='True K')
    axes[1].plot(kalman_results['time'], kalman_results['est_K'], 'c--', label='Estimated K')
    axes[1].set_ylabel('Parameter K')
    axes[1].legend(loc='upper left')
    axes[1].grid(True)

    ax1_twin = axes[1].twinx()
    ax1_twin.plot(kalman_results['time'], kalman_results['true_T'], 'r-', label='True T')
    ax1_twin.plot(kalman_results['time'], kalman_results['est_T'], 'm--', label='Estimated T')
    ax1_twin.set_ylabel('Parameter T (s)')
    ax1_twin.legend(loc='upper right')

    axes[1].set_xlabel('Time (s)')
    axes[1].set_title('Kalman Filter Parameter Tracking')

    plt.tight_layout()
    plt.savefig("mpc_comparison_results.png")
    print("Saved results plot to mpc_comparison_results.png")
    # plt.show()

if __name__ == "__main__":
    run_mpc_comparison()
