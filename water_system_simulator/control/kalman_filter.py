import numpy as np

class KalmanFilter:
    """
    A simple Kalman filter for state estimation.
    """
    def __init__(self, F, H, Q, R, x0, P0):
        """
        Initializes the Kalman filter.

        Args:
            F (np.ndarray): The state transition matrix.
            H (np.ndarray): The measurement matrix.
            Q (np.ndarray): The process noise covariance matrix.
            R (np.ndarray): The measurement noise covariance matrix.
            x0 (np.ndarray): The initial state estimate.
            P0 (np.ndarray): The initial estimate covariance.
        """
        self.F = F
        self.H = H
        self.Q = Q
        self.R = R
        self.x = x0
        self.P = P0

    def predict(self):
        """
        Performs the prediction step.
        """
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        return self.x

    def update(self, z):
        """
        Performs the update step.

        Args:
            z (np.ndarray): The measurement.
        """
        y = z - self.H @ self.x
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        self.x = self.x + K @ y
        self.P = (np.eye(self.P.shape[0]) - K @ self.H) @ self.P
        return self.x
