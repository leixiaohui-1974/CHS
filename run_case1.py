import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from water_system_simulator.engine import Simulator
from water_system_simulator.identification.least_squares import identify_time_constant
from water_system_simulator.modeling.storage_models import FirstOrderInertiaModel
from water_system_simulator.control.kalman_filter import KalmanFilter
from water_system_simulator.basic_tools.solvers import EulerIntegrator

def run_kalman_filter_test(dt: float):
    """
    Generates noisy data and uses the Kalman Filter to estimate the state.
    """
    print("\n--- Running Kalman Filter State Estimation Test ---")
    time_constant = 5.0
    A = np.array([[1 - dt / time_constant]])
    H = np.array([[1.0]])
    process_noise_std = 0.1
    measurement_noise_std = 0.5
    Q = np.array([[process_noise_std**2]])
    R = np.array([[measurement_noise_std**2]])

    duration = 100
    tank = FirstOrderInertiaModel(initial_storage=0.5, time_constant=time_constant, solver_class=None, dt=dt)
    # Manually step for this test since we need to inject noise
    tank.solver.f = lambda t, y: ( (np.sin(t/10*2)*2.0+2.5) + np.random.normal(0, process_noise_std) ) - y / time_constant

    true_storage = [0.5]
    for i in range(int(duration/dt)):
        true_storage.append(tank.solver.step(i*dt, true_storage[-1]))
    true_storage = np.array(true_storage[1:])
    noisy_measurements = true_storage + np.random.normal(0, measurement_noise_std, size=true_storage.shape)

    kf = KalmanFilter(F=A, H=H, Q=Q, R=R, x0=np.array([0.5]), P0=np.eye(1))
    estimated_storage = []

    for z in noisy_measurements:
        kf.predict()
        estimated_state = kf.update(np.array([z]))
        estimated_storage.append(estimated_state[0])

    plt.figure(figsize=(14, 8))
    plt.plot(true_storage, label='True Storage', color='blue')
    plt.plot(noisy_measurements, 'x', label='Noisy Measurements', color='gray', alpha=0.6)
    plt.plot(estimated_storage, label='Kalman Filter Estimate', color='red', linestyle='--')
    plt.title('Case 1: Kalman Filter State Estimation')
    plt.xlabel('Time (s)')
    plt.ylabel('Water Level (m)')
    plt.legend()
    plt.grid(True)
    plt.savefig('results/case1_kalman_filter_test.png')
    print("Kalman filter test plot saved.")

def main():
    if not os.path.exists('results'):
        os.makedirs('results')
    run_kalman_filter_test(dt=1.0)

if __name__ == "__main__":
    main()
