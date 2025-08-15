import numpy as np
from scipy.linalg import cho_factor, cho_solve

class KalmanFilter:
    """
    A general-purpose Kalman filter for state estimation.

    This implementation provides a clear and robust foundation for linear state
    estimation tasks. It is designed to be easily integrated into various
    agents or control systems that require filtering of noisy data to
    estimate the internal state of a system.
    """
    def __init__(self, F: np.ndarray, H: np.ndarray, Q: np.ndarray, R: np.ndarray, x0: np.ndarray, P0: np.ndarray):
        """
        Initializes the Kalman Filter.

        Args:
            F (np.ndarray): State transition matrix. Maps the state from time
                            k-1 to k.
            H (np.ndarray): Measurement matrix. Maps the state to the measurement
                            space.
            Q (np.ndarray): Process noise covariance matrix. Represents the
                            uncertainty in the process model.
            R (np.ndarray): Measurement noise covariance matrix. Represents the
                            uncertainty in the measurement.
            x0 (np.ndarray): Initial state estimate.
            P0 (np.ndarray): Initial estimate covariance. Represents the
                            uncertainty of the initial state estimate.
        """
        self.F = F
        self.H = H
        self.Q = Q
        self.R = R
        self.x = x0
        self.P = P0

    def predict(self) -> np.ndarray:
        """
        Performs the prediction step of the filter (the "time update").

        This step projects the current state and covariance estimate forward in
        time using the process model.

        Returns:
            np.ndarray: The a priori state estimate for the next time step.
        """
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        return self.x

    def update(self, z: np.ndarray):
        """
        Performs the update step of the filter (the "measurement update").

        This step corrects the predicted state estimate using a new measurement,
        blending the prediction with the measurement based on their respective
        uncertainties.

        Args:
            z (np.ndarray): The measurement at the current time step.
        """
        # Innovation or measurement residual
        y = z - self.H @ self.x

        # Innovation covariance
        S = self.H @ self.P @ self.H.T + self.R

        # Optimal Kalman gain calculation
        # We use Cholesky decomposition for its numerical stability and
        # efficiency with symmetric positive definite matrices like S.
        try:
            L, low = cho_factor(S)
            # Solve S @ K.T = H @ P for K.T, then transpose to get K
            K_T = cho_solve((L, low), self.H @ self.P)
            K = K_T.T
        except np.linalg.LinAlgError:
            # Fallback to using the pseudo-inverse if Cholesky decomposition fails
            # (e.g., if S is not positive-definite for some reason).
            K = self.P @ self.H.T @ np.linalg.pinv(S)

        # Update the state estimate (a posteriori state)
        self.x = self.x + K @ y

        # Update the estimate covariance (a posteriori covariance)
        I = np.eye(self.P.shape[0])
        self.P = (I - K @ self.H) @ self.P

    def get_state(self) -> np.ndarray:
        """
        Returns the current state estimate (the a posteriori estimate).

        Returns:
            np.ndarray: The current best estimate of the state.
        """
        return self.x

    def get_covariance(self) -> np.ndarray:
        """
        Returns the current estimate covariance.

        Returns:
            np.ndarray: The covariance matrix of the current state estimate.
        """
        return self.P
