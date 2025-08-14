import numpy as np
from .mpc_controller import MPCController
from ..modeling.integral_plus_delay_model import IntegralPlusDelayModel

class GainScheduledMPCController(MPCController):
    """
    A Gain-Scheduled Model Predictive Control (MPC) controller.
    This controller extends the standard MPC by adapting to changing system
    dynamics. It selects a linear model from a predefined 'model bank'
    based on a scheduling variable (e.g., current inflow or water level),
    and uses that model for prediction and optimization.
    """
    def __init__(self,
                 model_bank: list,
                 initial_model_params: dict,
                 dt: float,
                 **kwargs):
        """
        Initializes the Gain-Scheduled MPC controller.

        Args:
            model_bank (list): A list of dictionaries, where each dictionary
                               defines a model for a specific operating range.
                               Example: [{"threshold": 300, "K": 0.008, "T": 2000}, ...]
                               The list must be sorted by 'threshold'.
            initial_model_params (dict): Parameters for the initial prediction model,
                                         e.g., {'K': 0.01, 'T': 1800.0}.
            dt (float): The simulation time step, required to instantiate the prediction model.
            **kwargs: Keyword arguments to be passed to the parent MPCController,
                      such as prediction_horizon, control_horizon, set_point, etc.
        """
        if not model_bank:
            raise ValueError("The model_bank cannot be empty.")
        if not all('threshold' in m and 'K' in m and 'T' in m for m in model_bank):
            raise ValueError("Each model in model_bank must contain 'threshold', 'K', and 'T'.")

        # Sort the bank by threshold to ensure correct model selection
        self.model_bank = sorted(model_bank, key=lambda x: x['threshold'])
        self.active_model_params = None

        # The prediction model is an IntegralPlusDelayModel, which is updated on the fly.
        # We initialize it with some starting parameters.
        prediction_model = IntegralPlusDelayModel(
            K=initial_model_params['K'],
            T=initial_model_params['T'],
            dt=dt,
            initial_value=0  # Initial value is not critical here as it's synced at each step
        )

        super().__init__(prediction_model=prediction_model, **kwargs)

    def _select_model_params(self, scheduling_variable: float) -> dict:
        """Selects the appropriate model parameters from the bank."""
        # Find the first model whose threshold is greater than the scheduling variable.
        for model_params in self.model_bank:
            if scheduling_variable < model_params['threshold']:
                return model_params
        # If no threshold is met, it means the variable is >= the last threshold.
        # In this case, we use the last model in the bank.
        return self.model_bank[-1]

    def step(self, current_state: float, scheduling_variable: float, **kwargs):
        """
        Calculates the optimal control output for the current operating condition.

        Args:
            current_state (float): The latest measurement of the system's output.
            scheduling_variable (float): The variable that determines which model to use.
            **kwargs: Other keyword arguments for the parent step method, like disturbance_forecast.

        Returns:
            float: The first optimal control input.
        """
        # 1. Model Scheduling: Select the best model from the bank
        new_model_params = self._select_model_params(scheduling_variable)

        # 2. Update Model: If the model has changed, update the internal prediction model
        if new_model_params != self.active_model_params:
            self.active_model_params = new_model_params
            self.prediction_model.K = new_model_params['K']
            self.prediction_model.T = new_model_params['T']
            # Re-calculate delay steps based on new T
            self.prediction_model.delay_steps = int(round(new_model_params['T'] / self.prediction_model.dt))
            print(f"GS-MPC: Switched to model K={self.prediction_model.K}, T={self.prediction_model.T}")

        # 3. Optimize & Execute: Call the parent's step method with the updated model
        return super().step(current_state=current_state, **kwargs)

    def get_state(self):
        """Returns the controller's state, including active model parameters."""
        parent_state = super().get_state()
        if self.active_model_params:
            parent_state['active_K'] = self.active_model_params['K']
            parent_state['active_T'] = self.active_model_params['T']
        else:
            parent_state['active_K'] = None
            parent_state['active_T'] = None
        return parent_state
