import numpy as np
from .kalman_filter import KalmanFilter

class KFParameterEstimator:
    """
    A wrapper to use a linear Kalman Filter for single parameter estimation.
    """
    def __init__(self, initial_param_guess, process_noise, measurement_noise):
        """
        Initializes the parameter estimator.

        Args:
            initial_param_guess (float): The initial guess for the parameter value.
            process_noise (float): The variance of the process noise (Q).
                                   Represents uncertainty in the parameter's stability.
            measurement_noise (float): The variance of the measurement noise (R).
                                       Represents uncertainty in the observation.
        """
        # The state 'x' is the parameter we want to estimate.
        # The state transition model is x_k = x_{k-1} + w_k, where w_k is process noise.
        # So, the state transition matrix F = 1.
        F = np.array([[1.]])

        # The measurement model is z_k = H_k * x_k + v_k, where v_k is measurement noise.
        # H_k is the measurement matrix, which we must provide at each step.
        # We initialize it to zero here.
        H = np.array([[0.]])

        # Process noise covariance Q
        Q = np.array([[process_noise]])

        # Measurement noise covariance R
        R = np.array([[measurement_noise]])

        # Initial state estimate (our parameter guess)
        x0 = np.array([[initial_param_guess]])

        # Initial estimate covariance (how certain we are about our initial guess)
        P0 = np.array([[1.]]) # Start with some uncertainty

        self.kf = KalmanFilter(F=F, H=H, Q=Q, R=R, x0=x0, P0=P0)

    def run_step(self, measurement, measurement_matrix_H):
        """
        Performs one step of prediction and update.

        Args:
            measurement (float): The observed value (z_k), e.g., pseudo-observed runoff.
            measurement_matrix_H (float): The value for the measurement matrix H at this step.
                                          e.g., total precipitation for the day.

        Returns:
            float: The updated parameter estimate.
        """
        # 1. Prediction step
        self.kf.predict()

        # 2. Update step
        # The H matrix is time-variant and must be updated at each step
        self.kf.H = np.array([[measurement_matrix_H]])

        z = np.array([[measurement]])
        updated_state = self.kf.update(z)

        return updated_state[0, 0]

    @property
    def current_estimate(self):
        """Returns the current best estimate of the parameter."""
        return self.kf.x[0, 0]
