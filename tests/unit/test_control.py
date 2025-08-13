import unittest
import numpy as np
from water_system_simulator.control.kalman_filter import KalmanFilter

class TestControl(unittest.TestCase):

    def test_kalman_filter_numerical_stability(self):
        """
        Tests the Kalman filter's numerical stability with an ill-conditioned system.
        """
        # Create an ill-conditioned system
        F = np.eye(2)
        H = np.array([[1, 1e-4], [1, -1e-4]])
        Q = 1e-5 * np.eye(2)
        R = np.eye(2)
        x0 = np.zeros(2)
        P0 = np.eye(2)

        kf = KalmanFilter(F=F, H=H, Q=Q, R=R, x0=x0, P0=P0)

        # A measurement that could cause issues
        z = np.array([1, 1])

        # The update step involves inverting S = H @ P @ H.T + R
        # For an ill-conditioned H, S can be close to singular.
        # Using cho_solve should be more stable than np.linalg.inv
        kf.predict()
        kf.update(z)

        # Assert that the state is not NaN and is a reasonable value
        self.assertFalse(np.isnan(kf.x).any())
        # The exact value is not critical, just that it's a stable result
        self.assertTrue(np.all(np.isfinite(kf.x)))
