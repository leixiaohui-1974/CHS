import cvxpy as cp
import numpy as np
from .base_controller import BaseController

class MPCController(BaseController):
    """
    A Model Predictive Control (MPC) controller for linear time-invariant (LTI) systems,
    with feedforward disturbance rejection.
    """
    def __init__(self, A, B, Q, R, N, setpoint, u_min=None, u_max=None, x_min=None, x_max=None, **kwargs):
        """
        Initializes the MPC controller.

        Args:
            A (np.ndarray): The state transition matrix.
            B (np.ndarray): The input matrix for the control variable u.
            Q (list or np.ndarray): State weighting cost.
            R (list or np.ndarray): Input weighting cost.
            N (int): The prediction horizon.
            setpoint (float): The desired state setpoint.
            ...
        """
        super().__init__(**kwargs)
        A = np.array(A)
        B = np.array(B)

        n_x = A.shape[0]
        n_u = B.shape[1]

        q_val = np.array(Q).flatten()[0]
        Q_matrix = np.zeros((n_x, n_x))
        Q_matrix[0, 0] = q_val

        r_val = np.array(R).flatten()[0]
        R_matrix = np.diag([r_val] * n_u)

        sp_val = np.array(setpoint).flatten()[0]
        setpoint_vec = np.zeros(n_x)
        setpoint_vec[0] = sp_val

        self.A = A
        self.B = B
        self.Q = Q_matrix
        self.R = R_matrix
        self.N = N
        self.setpoint = setpoint_vec
        self.output = 0.0

        self.u_min = u_min
        self.u_max = u_max
        self.x_min = x_min
        self.x_max = x_max

        # CVXPY problem setup
        self.x = cp.Variable((n_x, N + 1))
        self.u = cp.Variable((n_u, N))
        self.d = cp.Parameter((n_u, N), value=np.zeros((n_u, N))) # Disturbance forecast

        self.objective = 0
        self.constraints = []

        for k in range(N):
            # The disturbance is assumed to affect the system via the same input matrix B
            self.constraints += [self.x[:, k+1] == self.A @ self.x[:, k] + self.B @ (self.u[:, k] + self.d[:, k])]
            self.objective += cp.quad_form(self.x[:, k] - self.setpoint, self.Q) + cp.quad_form(self.u[:, k], self.R)
            if self.u_min is not None:
                self.constraints += [self.u[:, k] >= self.u_min]
            if self.u_max is not None:
                self.constraints += [self.u[:, k] <= self.u_max]
            if self.x_min is not None:
                self.constraints += [self.x[0, k] >= self.x_min]
            if self.x_max is not None:
                self.constraints += [self.x[0, k] <= self.x_max]

        self.objective += cp.quad_form(self.x[:, self.N] - self.setpoint, self.Q)

        self.x0 = cp.Parameter(n_x)
        self.constraints += [self.x[:, 0] == self.x0]

        self.problem = cp.Problem(cp.Minimize(self.objective), self.constraints)
        print("MPC Controller with disturbance rejection initialized successfully.")

    def step(self, measured_value, disturbance=0.0, dt=None, **kwargs):
        """
        Calculates the optimal control output.
        Args:
            measured_value (float): The current state.
            disturbance (float): The current measured disturbance.
        """
        current_state = np.zeros(self.A.shape[0])
        current_state[0] = measured_value
        for i in range(1, len(current_state)):
            current_state[i] = self.output
        self.x0.value = current_state

        # Assume disturbance is constant over the horizon
        disturbance_forecast = np.tile(disturbance, (self.N, 1)).T
        self.d.value = disturbance_forecast

        try:
            self.problem.solve(solver=cp.OSQP, warm_start=True)
            if self.problem.status in ["infeasible", "unbounded"]:
                print(f"Warning: MPC problem is {self.problem.status}. Returning zero control.")
                self.output = 0.0
            else:
                self.output = self.u.value[0, 0]
        except Exception as e:
            print(f"Error during MPC solve: {e}. Returning zero control.")
            self.output = 0.0

        return self.output

    def get_state(self):
        return {"output": self.output}
