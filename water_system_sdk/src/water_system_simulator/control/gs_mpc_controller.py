import cvxpy as cp
import numpy as np
from .base_controller import BaseController
from ..utils.model_conversion import integral_delay_to_ss

class GainScheduledMPCController(BaseController):
    """
    A Gain-Scheduled Model Predictive Control (MPC) controller.

    This controller adapts to changing system dynamics by selecting a linear
    model from a predefined 'model bank' based on a scheduling variable.
    It is designed for systems that operate under varying conditions,
    where a single linear model is insufficient.
    """
    def __init__(self, model_bank: list, Q: list, R: list, N: int, dt: float,
                 setpoint: float, u_min: float = None, u_max: float = None,
                 x_min: float = None, x_max: float = None, **kwargs):
        """
        Initializes the Gain-Scheduled MPC controller.

        Args:
            model_bank (list): A list of dictionaries, where each dictionary
                               defines a model for a specific operating range.
                               e.g., [{"threshold": 300, "K": 0.008, "T": 2000}, ...]
            Q (list): The state weighting cost. Should be a list with one value, e.g., [1].
            R (list): The input weighting cost. Should be a list with one value, e.g., [0.1].
            N (int): The prediction horizon.
            dt (float): The simulation time step, crucial for model discretization.
            setpoint (float): The desired state setpoint.
            u_min (float, optional): Minimum control input.
            u_max (float, optional): Maximum control input.
            x_min (float, optional): Minimum state value.
            x_max (float, optional): Maximum state value.
        """
        super().__init__(**kwargs)
        if not model_bank:
            raise ValueError("The model_bank cannot be empty.")

        self.model_bank = sorted(model_bank, key=lambda x: x['threshold'])
        self.Q_weight = np.array(Q).flatten()[0]
        self.R_weight = np.array(R).flatten()[0]
        self.N = N
        self.dt = dt
        self.setpoint_val = setpoint
        self.u_min = u_min
        self.u_max = u_max
        self.x_min = x_min
        self.x_max = x_max
        self.output = 0.0

        # Cache for the currently active model and CVXPY problem
        self._active_model_params = None
        self._problem = None
        self._x0 = None
        self._u = None

    def _select_model(self, scheduling_variable: float) -> dict:
        """Selects the appropriate model from the bank based on the scheduling variable."""
        for model in self.model_bank:
            if scheduling_variable < model['threshold']:
                return model
        # If no threshold is met, return the last model (for values >= last threshold)
        return self.model_bank[-1]

    def _create_problem(self, model_params: dict):
        """Creates or re-creates the CVXPY optimization problem."""
        K = model_params['K']
        T = model_params['T']
        self._active_model_params = model_params

        A, B = integral_delay_to_ss(K, T, self.dt)
        n = A.shape[0]  # state dimension
        m = B.shape[1]  # input dimension

        x = cp.Variable((n, self.N + 1))
        u = cp.Variable((m, self.N))
        x0 = cp.Parameter(n)

        # We only penalize the first state (the actual output)
        Q_matrix = np.zeros((n, n))
        Q_matrix[0, 0] = self.Q_weight
        R_matrix = np.array([[self.R_weight]])

        objective = 0
        constraints = [x[:, 0] == x0]

        # Desired setpoint for the state vector
        setpoint_vec = np.zeros(n)
        setpoint_vec[0] = self.setpoint_val

        for k in range(self.N):
            objective += cp.quad_form(x[:, k] - setpoint_vec, Q_matrix) + cp.quad_form(u[:, k], R_matrix)
            constraints += [x[:, k+1] == A @ x[:, k] + B @ u[:, k]]
            if self.u_min is not None:
                constraints += [u[0, k] >= self.u_min]
            if self.u_max is not None:
                constraints += [u[0, k] <= self.u_max]
            if self.x_min is not None:
                constraints += [x[0, k] >= self.x_min]
            if self.x_max is not None:
                constraints += [x[0, k] <= self.x_max]

        objective += cp.quad_form(x[:, self.N] - setpoint_vec, Q_matrix)

        self._problem = cp.Problem(cp.Minimize(objective), constraints)
        self._x0 = x0
        self._u = u
        print(f"MPC problem re-created for K={K}, T={T} (State dim: {n})")


    def step(self, measured_value: float, scheduling_variable: float, **kwargs):
        """
        Calculates the optimal control output for the current operating condition.

        Args:
            measured_value (float): The current measured state value (e.g., water level).
            scheduling_variable (float): The variable that determines which model to use.

        Returns:
            float: The first optimal control input.
        """
        model_params = self._select_model(scheduling_variable)

        if model_params != self._active_model_params:
            self._create_problem(model_params)

        current_state = np.zeros(self._x0.shape)
        current_state[0] = measured_value
        for i in range(1, len(current_state)):
            current_state[i] = self.output
        self._x0.value = current_state

        try:
            self._problem.solve(solver=cp.OSQP, warm_start=True)

            if self._problem.status in ["infeasible", "unbounded"]:
                print(f"Warning: GS-MPC problem is {self._problem.status}. Returning zero control.")
                self.output = 0.0
            else:
                self.output = self._u.value[0, 0]
        except Exception as e:
            print(f"Error during GS-MPC solve: {e}. Returning zero control.")
            self.output = 0.0

        return self.output

    def get_state(self):
        return {"output": self.output, "active_K": self._active_model_params['K'], "active_T": self._active_model_params['T']}
