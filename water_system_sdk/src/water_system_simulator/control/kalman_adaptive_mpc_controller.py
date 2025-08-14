from .mpc_controller import MPCController
from ..modeling.integral_plus_delay_model import IntegralPlusDelayModel

class KalmanAdaptiveMPCController(MPCController):
    """
    A Kalman-Adaptive Model Predictive Control (MPC) controller.
    This advanced controller collaborates with an external parameter estimator,
    such as a Kalman Filter, to continuously update its internal prediction model.
    This allows the MPC to adapt to time-varying system dynamics in real-time.
    """
    def __init__(self,
                 initial_model_params: dict,
                 dt: float,
                 **kwargs):
        """
        Initializes the Kalman-Adaptive MPC controller.

        Args:
            initial_model_params (dict): A dictionary with the initial parameters
                                         for the prediction model, e.g., {'K': 0.01, 'T': 1800.0}.
            dt (float): The simulation time step, required to instantiate the prediction model.
            **kwargs: Keyword arguments to be passed to the parent MPCController,
                      such as prediction_horizon, control_horizon, set_point, etc.
        """
        # The prediction model is an IntegralPlusDelayModel, which is updated on the fly.
        # We initialize it with some best-guess starting parameters.
        prediction_model = IntegralPlusDelayModel(
            K=initial_model_params['K'],
            T=initial_model_params['T'],
            dt=dt,
            initial_value=0  # This is synced at each step, so initial value is not critical
        )

        super().__init__(prediction_model=prediction_model, **kwargs)
        self.updated_params = initial_model_params.copy()

    def step(self, current_state: float, updated_model_params: dict, **kwargs):
        """
        Calculates the optimal control output using the latest model parameters.

        Args:
            current_state (float): The latest measurement of the system's output.
            updated_model_params (dict): A dictionary with the most recent parameter
                                         estimates from an external source (e.g., Kalman filter).
                                         Example: {'K': 0.0085, 'T': 1750.0}
            **kwargs: Other keyword arguments for the parent step method, like disturbance_forecast.

        Returns:
            float: The first optimal control input.
        """
        # 1. Model Update: Update the internal model with the new parameters
        if updated_model_params:
            if self.prediction_model.K != updated_model_params.get('K') or \
               self.prediction_model.T != updated_model_params.get('T'):

                new_K = updated_model_params.get('K', self.prediction_model.K)
                new_T = updated_model_params.get('T', self.prediction_model.T)

                self.prediction_model.K = new_K
                self.prediction_model.T = new_T
                self.prediction_model.delay_steps = int(round(new_T / self.prediction_model.dt))

                self.updated_params = {'K': new_K, 'T': new_T}
                # Optional: print a message when the model is updated
                # print(f"Kalman-MPC: Updated model to K={new_K:.4f}, T={new_T:.1f}")


        # 2. Optimize & Execute: Call the parent's step method with the updated model
        return super().step(current_state=current_state, **kwargs)

    def get_state(self):
        """Returns the controller's state, including the currently active model parameters."""
        parent_state = super().get_state()
        parent_state.update(self.updated_params)
        return parent_state
