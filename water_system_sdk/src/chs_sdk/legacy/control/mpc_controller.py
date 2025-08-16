import cvxpy as cp
import numpy as np
import copy
from .base_controller import BaseController
from ..modeling.base_model import BaseModel

class MPCController(BaseController):
    """
    A Model Predictive Control (MPC) controller that uses a simulation model
    for prediction. It is designed to work with models that follow the
    BaseModel interface.
    """
    def __init__(self,
                 prediction_model: BaseModel,
                 prediction_horizon: int,
                 control_horizon: int,
                 set_point: float,
                 q_weight: float = 1.0,
                 r_weight: float = 0.1,
                 u_min: float = -np.inf,
                 u_max: float = np.inf,
                 **kwargs):
        """
        Initializes the MPC controller.

        Args:
            prediction_model (BaseModel): An instance of a model used for prediction.
                                          This model should have 'step' and 'get_state' methods.
            prediction_horizon (int): (P) The number of future steps to predict.
            control_horizon (int): (M) The number of future control moves to optimize.
                                   Must be <= prediction_horizon.
            set_point (float): The desired value for the system's output.
            q_weight (float): Weight for the state deviation term in the objective function.
            r_weight (float): Weight for the control effort term in the objective function.
            u_min (float): Minimum allowable control input.
            u_max (float): Maximum allowable control input.
        """
        super().__init__(**kwargs)

        if not isinstance(prediction_model, BaseModel):
            raise TypeError("prediction_model must be a subclass of BaseModel.")
        if not (control_horizon <= prediction_horizon and control_horizon > 0):
            raise ValueError("Control horizon M must be > 0 and <= prediction_horizon P.")

        self.prediction_model = prediction_model
        self.P = prediction_horizon
        self.M = control_horizon
        self.set_point = set_point
        self.q_weight = q_weight
        self.r_weight = r_weight
        self.u_min = u_min
        self.u_max = u_max

        # The last optimal control sequence found
        self.last_optimal_u = np.zeros(self.M)
        self.current_control_action = 0.0

        # --- CVXPY Problem Setup ---
        self.u_M = cp.Variable(self.M, name="u_M")
        self.x_P = cp.Variable(self.P + 1, name="x_P")
        self.x_init = cp.Parameter(1, name="x_init")

        # Parameters for the affine prediction model at each step
        # These will be updated at each time step based on the model simulation
        self.A_pred = cp.Parameter((self.P, 1), name="A_pred")
        self.B_pred = cp.Parameter((self.P, self.M), name="B_pred")
        self.C_pred = cp.Parameter(self.P, name="C_pred")

        objective = 0
        constraints = [self.x_P[0] == self.x_init]

        # Build the objective function
        for k in range(self.P):
            objective += self.q_weight * cp.power(self.x_P[k+1] - self.set_point, 2)
        for k in range(self.M):
            objective += self.r_weight * cp.power(self.u_M[k], 2)

        # Add constraints on control inputs
        constraints += [self.u_M >= self.u_min, self.u_M <= self.u_max]

        # Add the system dynamics constraint
        # x_P[1:] represents the predicted states from k=1 to k=P
        # This is a compact way to represent the linear system evolution
        # x_pred = A*x_current + B*u_sequence + C
        constraints += [self.x_P[1:] == self.A_pred @ self.x_init + self.B_pred @ self.u_M + self.C_pred]

        self.problem = cp.Problem(cp.Minimize(objective), constraints)

    def _linearize_model_at_point(self, model_instance: BaseModel, current_state: float, disturbance_forecast: np.ndarray):
        """
        Linearizes the prediction model around the current operating point.
        This version uses a step-response method to build an affine model:
        x_pred = A*x_current + B*u_sequence + C
        where C captures the effect of disturbances and model nonlinearities.
        """
        # Ensure the disturbance forecast has length P
        if len(disturbance_forecast) < self.P:
            disturbance_forecast = np.pad(disturbance_forecast, (0, self.P - len(disturbance_forecast)), 'edge')

        # 1. Find the free response (C term): effect of disturbances and initial state
        model_c = copy.deepcopy(model_instance)
        # Set the model to the current state
        model_c.state.output = current_state
        free_response = np.zeros(self.P)
        for i in range(self.P):
            # Use the forecasted disturbance for this step
            model_c.input.inflow = disturbance_forecast[i]
            # No control input for the free response
            model_c.input.control_inflow = 0.0
            model_c.step()
            free_response[i] = model_c.get_state()['output']

        # 2. Find the forced response (B term): effect of control inputs
        B = np.zeros((self.P, self.M))
        # A small perturbation for the control input
        delta_u = 1e-5
        for j in range(self.M):  # For each control move in the control horizon
            model_b = copy.deepcopy(model_instance)
            model_b.state.output = current_state

            # Apply a perturbation delta_u at step j and keep it for subsequent steps
            # This is a step response, not an impulse response
            u_sequence = np.zeros(self.P)
            u_sequence[j:] = delta_u

            forced_response_j = np.zeros(self.P)
            for i in range(self.P):
                model_b.input.inflow = disturbance_forecast[i]
                model_b.input.control_inflow = u_sequence[i]
                model_b.step()
                forced_response_j[i] = model_b.get_state()['output']

            # The B matrix column is the difference from the free response, scaled by delta_u
            B[:, j] = (forced_response_j - free_response) / delta_u

        # 3. The A term is simply the influence of the initial state on future states.
        # For our formulation x_pred = A*x_current + B*u + C, we can simplify.
        # The free_response already contains the evolution from x_current.
        # So, we can set A=0 and C = free_response.
        # This makes the model: x_pred(k) = free_response(k) + sum(B(k,j)*u(j))
        A = np.zeros((self.P, 1))
        C = free_response

        return A, B, C


    def step(self, current_state: float, disturbance_forecast: np.ndarray = np.array([]), **kwargs):
        """
        Calculates the optimal control action for the current time step.

        Args:
            current_state (float): The latest measurement of the system's output.
            disturbance_forecast (np.ndarray, optional): A forecast of future disturbances.
                                                          Defaults to an empty array.

        Returns:
            float: The optimal control action for the current step.
        """
        # 1. Linearize the model to get A, B, C parameters for the optimizer
        A, B, C = self._linearize_model_at_point(self.prediction_model, current_state, disturbance_forecast)

        # Update CVXPY parameters
        self.x_init.value = np.array([current_state])
        self.A_pred.value = A
        self.B_pred.value = B
        self.C_pred.value = C

        # 2. Optimize: Solve the QP problem for the optimal control sequence u_M
        try:
            self.problem.solve(solver=cp.OSQP, warm_start=True)

            if self.problem.status in ["infeasible", "unbounded"]:
                print(f"Warning: MPC problem is {self.problem.status}. Holding last known good control.")
                # Keep the last control action if optimization fails
            else:
                self.last_optimal_u = self.u_M.value
        except Exception as e:
            print(f"Error during MPC solve: {e}. Holding last known good control.")

        # 3. Execute: Apply only the first element of the optimal sequence
        self.current_control_action = self.last_optimal_u[0]

        return self.current_control_action

    def get_state(self):
        """Returns the current state of the controller (its latest output)."""
        return {'output': self.current_control_action}
