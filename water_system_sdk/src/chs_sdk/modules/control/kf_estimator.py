import numpy as np
from chs_sdk.modeling.base_model import BaseModel

class ParameterKalmanFilterAgent(BaseModel):
    """
    An agent that uses a Kalman Filter to estimate the parameters of a linear system.
    This approach treats the parameters as the state to be estimated.
    """
    def __init__(self, initial_params: dict, process_noise_Q: float, measurement_noise_R: float, **kwargs):
        """
        Initializes the Parameter Kalman Filter estimator.

        Args:
            initial_params (dict): A dictionary of initial parameter guesses.
            process_noise_Q (float): The variance of the process noise. This models the
                                     uncertainty in the parameter dynamics (i.e., how much
                                     the parameters might change over time). A small non-zero
                                     value allows the filter to remain adaptive.
            measurement_noise_R (float): The variance of the measurement noise. This
                                         represents the accuracy of the `observed_outflow`.
        """
        super().__init__(**kwargs)
        self.param_names = sorted(initial_params.keys())

        # The state vector 'x' is the parameter vector 'theta'
        self.x = np.array([initial_params[key] for key in self.param_names]).reshape(-1, 1)

        # The state covariance matrix
        self.P = np.eye(len(self.param_names)) * 1000.0

        # The process noise covariance matrix Q
        # Assumes independent noise for each parameter
        self.Q = np.eye(len(self.param_names)) * process_noise_Q

        # The measurement noise covariance R (a scalar in this SISO case)
        self.R = measurement_noise_R

        # Internal state for constructing the observation matrix H
        self.prev_inflow = 0.0
        self.prev_outflow = 0.0

        self.output = self.get_state()

    def step(self, inflow: float, observed_outflow: float):
        """
        Performs one "predict-update" cycle of the Kalman Filter.

        This implementation assumes a first-order model of the form:
        y(k) = a1 * y(k-1) + b1 * u(k-1)
        The state is x = [a1, b1].T
        The observation is y(k).
        The observation matrix is H = [y(k-1), u(k-1)].

        Args:
            inflow (float): The current input to the system, u(k).
            observed_outflow (float): The current measured output, y(k).
        """
        # --- 1. Predict Step ---
        # State prediction: parameters are assumed constant, so x_pred = x
        # F is the identity matrix, so x_k|k-1 = x_k-1|k-1
        x_pred = self.x

        # Covariance prediction: P_k|k-1 = P_k-1|k-1 + Q
        # (since F=I, F*P*F.T = P)
        P_pred = self.P + self.Q

        # --- 2. Update Step ---
        # Construct the observation matrix H from the previous step's data
        H = np.array([[self.prev_outflow, self.prev_inflow]])

        # Calculate innovation (prediction error)
        y = observed_outflow - (H @ x_pred)

        # Calculate innovation covariance
        S = H @ P_pred @ H.T + self.R

        # Calculate Kalman Gain
        K = P_pred @ H.T @ np.linalg.inv(S)

        # Update state estimate
        self.x = x_pred + K * y

        # Update covariance estimate
        I = np.eye(self.x.shape[0])
        self.P = (I - K @ H) @ P_pred

        # --- Update internal state for the next iteration ---
        self.prev_inflow = inflow
        self.prev_outflow = observed_outflow

        self.output = self.get_state()
        return self.output

    def get_state(self):
        """
        Returns the current estimates of the parameters.

        Returns:
            dict: A dictionary mapping parameter names to their current estimated values.
        """
        return {name: self.x[i][0] for i, name in enumerate(self.param_names)}
