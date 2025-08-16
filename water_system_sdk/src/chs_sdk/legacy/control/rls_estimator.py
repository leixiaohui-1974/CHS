import numpy as np
from water_system_simulator.modeling.base_model import BaseModel

class RecursiveLeastSquaresAgent(BaseModel):
    """
    An agent that uses the Recursive Least Squares (RLS) algorithm to estimate
    the parameters of a linear system model online.
    """
    def __init__(self, initial_params: dict, forgetting_factor: float = 0.98, **kwargs):
        """
        Initializes the RLS estimator.

        Args:
            initial_params (dict): A dictionary containing the initial guesses for
                                   the parameters. e.g., {'a1': 0.1, 'b1': 0.5}
            forgetting_factor (float): The forgetting factor (lambda) for the RLS algorithm.
                                       Values closer to 1 give more weight to past data.
        """
        super().__init__(**kwargs)
        # The sorted parameter names
        self.param_names = sorted(initial_params.keys())
        # The parameter vector
        self.theta = np.array([initial_params[key] for key in self.param_names]).reshape(-1, 1)
        # The covariance matrix, initialized to a large value
        self.P = np.eye(len(self.param_names)) * 1000.0
        self.forgetting_factor = forgetting_factor

        # Internal state to store previous values for constructing the regressor
        self.prev_inflow = 0.0
        self.prev_outflow = 0.0

    def step(self, inflow: float, observed_outflow: float):
        """
        Performs one iteration of the RLS algorithm.

        This implementation assumes a first-order model of the form:
        y(k) = a1 * y(k-1) + b1 * u(k-1)

        where y is the outflow and u is the inflow. The parameters to be
        estimated are 'a1' and 'b1'.

        Args:
            inflow (float): The current input to the system (u(k)).
            observed_outflow (float): The current measured output from the system (y(k)).
        """
        # For a first-order model, the regressor phi is [y(k-1), u(k-1)]
        # This needs to be updated based on the actual model structure.
        # For now, we assume the simple y(k) = a1*y(k-1) + b1*u(k-1) model
        phi = np.array([self.prev_outflow, self.prev_inflow]).reshape(-1, 1)

        # 1. Calculate Kalman Gain
        P_phi = self.P @ phi
        gain_numerator = P_phi
        gain_denominator = self.forgetting_factor + phi.T @ P_phi
        K = gain_numerator / gain_denominator

        # 2. Calculate Prediction Error
        prediction = phi.T @ self.theta
        error = observed_outflow - prediction

        # 3. Update Parameter Estimate
        self.theta = self.theta + K * error

        # 4. Update Covariance Matrix
        self.P = (1 / self.forgetting_factor) * (self.P - K @ phi.T @ self.P)

        # Update internal state for the next step
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
        return {name: self.theta[i][0] for i, name in enumerate(self.param_names)}
