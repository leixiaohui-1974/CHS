from abc import abstractmethod
import numpy as np
from scipy.linalg import cho_factor, cho_solve

from chs_sdk.modules.modeling.base_model import BaseModel


class BaseDataAssimilation(BaseModel):
    """
    Abstract base class for all data assimilation models.
    """

    def step(self, *args, **kwargs):
        """
        For data assimilation models, the step is a prediction.
        """
        return self.predict(*args, **kwargs)

    @abstractmethod
    def predict(self, *args, **kwargs):
        """
        Represents a single time step of the model's execution.

        This method must be implemented by subclasses. It can accept
        any arguments required for the simulation step.
        """
        pass

    @abstractmethod
    def update(self, observation: np.ndarray):
        """
        Updates the state of the model with a new observation.
        """
        pass

    @abstractmethod
    def get_state(self) -> np.ndarray:
        """
        Returns a dictionary of the model's current state.
        This must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def get_covariance(self) -> np.ndarray:
        """
        Returns the covariance of the model's current state.
        This must be implemented by subclasses.
        """
        pass


class ExtendedKalmanFilter(BaseDataAssimilation):
    """
    An Extended Kalman Filter for non-linear state estimation.
    """

    def __init__(self, f, h, F_jacobian, H_jacobian, Q, R, x0, P0):
        """
        Initializes the Extended Kalman Filter.
        Args:
            f (callable): The non-linear state transition function.
            h (callable): The non-linear measurement function.
            F_jacobian (callable): The Jacobian of the state transition function.
            H_jacobian (callable): The Jacobian of the measurement function.
            Q (np.ndarray): The process noise covariance matrix.
            R (np.ndarray): The measurement noise covariance matrix.
            x0 (np.ndarray): The initial state estimate.
            P0 (np.ndarray): The initial estimate covariance.
        """
        super().__init__()
        self.f = f
        self.h = h
        self.F_jacobian = F_jacobian
        self.H_jacobian = H_jacobian
        self.Q = Q
        self.R = R
        self.x = x0
        self.P = P0
        self.output = self.x

    def predict(self, *args, **kwargs):
        """
        Performs the prediction step using the non-linear state transition function.
        """
        F = self.F_jacobian(self.x, *args, **kwargs)
        self.x = self.f(self.x, *args, **kwargs)
        self.P = F @ self.P @ F.T + self.Q
        self.output = self.x
        return self.x

    def update(self, observation: np.ndarray):
        """
        Performs the update step using the non-linear measurement function.
        Args:
            observation (np.ndarray): The measurement.
        """
        H = self.H_jacobian(self.x)
        y = observation - self.h(self.x)
        S = H @ self.P @ H.T + self.R

        # It is more stable to solve for K using Cholesky decomposition
        try:
            L, low = cho_factor(S)
            # Solve S K^T = H P for K^T
            K_T = cho_solve((L, low), H @ self.P)
            K = K_T.T
        except np.linalg.LinAlgError:
            # Fallback to pseudo-inverse if Cholesky fails
            K = self.P @ H.T @ np.linalg.pinv(S)

        self.x = self.x + K @ y
        self.P = (np.eye(self.P.shape[0]) - K @ H) @ self.P
        self.output = self.x
        return self.x

    def get_state(self) -> np.ndarray:
        """
        Returns the current state estimate.
        """
        return self.x

    def get_covariance(self) -> np.ndarray:
        """
        Returns the current estimate covariance.
        """
        return self.P


class EnsembleKalmanFilter(BaseDataAssimilation):
    """
    An Ensemble Kalman Filter for non-linear state estimation, particularly
    useful for high-dimensional systems.
    """

    def __init__(self, f, h, Q, R, x0, P0, n_ensemble):
        """
        Initializes the Ensemble Kalman Filter.

        Args:
            f (callable): The non-linear state transition function.
            h (callable): The non-linear measurement function.
            Q (np.ndarray): The process noise covariance matrix.
            R (np.ndarray): The measurement noise covariance matrix.
            x0 (np.ndarray): The initial state estimate.
            P0 (np.ndarray): The initial estimate covariance.
            n_ensemble (int): The number of ensemble members.
        """
        super().__init__()
        self.f = f
        self.h = h
        self.Q = Q
        self.R = R
        self.n_ensemble = n_ensemble
        self.x = x0

        # Create the initial ensemble
        self.ensemble = np.random.multivariate_normal(x0, P0, n_ensemble).T
        self.P = P0
        self.output = self.x

    def predict(self, *args, **kwargs):
        """
        Performs the prediction step by propagating each ensemble member through
        the non-linear state transition function and adding process noise.
        """
        # Propagate each ensemble member
        for i in range(self.n_ensemble):
            self.ensemble[:, i] = self.f(self.ensemble[:, i], *args, **kwargs)

        # Add process noise
        self.ensemble += np.random.multivariate_normal(
            np.zeros(self.x.shape[0]), self.Q, self.n_ensemble
        ).T

        # Update the state estimate and covariance
        self.x = np.mean(self.ensemble, axis=1)
        self.P = np.cov(self.ensemble)
        self.output = self.x
        return self.x

    def update(self, observation: np.ndarray):
        """
        Performs the update step using the ensemble to compute the Kalman gain.

        Args:
            observation (np.ndarray): The measurement.
        """
        # Predict observations for each ensemble member
        predicted_obs = np.array([self.h(self.ensemble[:, i]) for i in range(self.n_ensemble)]).T
        if predicted_obs.ndim == 1:
            predicted_obs = predicted_obs.reshape(1, -1)

        # Add measurement noise to the observation for each ensemble member
        obs_ensemble = np.random.multivariate_normal(observation, self.R, self.n_ensemble).T
        if obs_ensemble.ndim == 1:
            obs_ensemble = obs_ensemble.reshape(1, -1)


        # Calculate Kalman gain
        P_xy = np.cov(self.ensemble, predicted_obs)[: self.x.shape[0], self.x.shape[0] :]
        P_yy = np.cov(predicted_obs)
        K = P_xy @ np.linalg.pinv(P_yy + self.R)

        # Update each ensemble member
        self.ensemble = self.ensemble + K @ (obs_ensemble - predicted_obs)

        # Update the state estimate and covariance
        self.x = np.mean(self.ensemble, axis=1)
        self.P = np.cov(self.ensemble)
        self.output = self.x
        return self.x

    def get_state(self) -> np.ndarray:
        """
        Returns the current state estimate.
        """
        return self.x

    def get_covariance(self) -> np.ndarray:
        """
        Returns the current estimate covariance.
        """
        return self.P
