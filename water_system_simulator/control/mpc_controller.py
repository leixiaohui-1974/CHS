import cvxpy as cp
import numpy as np
from .base_controller import BaseController

class MPCController(BaseController):
    """
    A Model Predictive Control (MPC) controller for linear time-invariant (LTI) systems.
    """
    def __init__(self, A, B, Q, R, N, setpoint, u_min=None, u_max=None, x_min=None, x_max=None, **kwargs):
        """
        Initializes the MPC controller.

        Args:
            A (np.ndarray): The state transition matrix.
            B (np.ndarray): The input matrix.
            Q (np.ndarray): The state weighting matrix.
            R (np.ndarray): The input weighting matrix.
            N (int): The prediction horizon.
            setpoint (np.ndarray): The desired state setpoint (reference).
            u_min (float, optional): Minimum control input. Defaults to None.
            u_max (float, optional): Maximum control input. Defaults to None.
            x_min (float, optional): Minimum state value. Defaults to None.
            x_max (float, optional): Maximum state value. Defaults to None.
        """
        super().__init__(**kwargs)
        # Ensure matrices are numpy arrays right away
        A = np.array(A)
        B = np.array(B)
        Q = np.array(Q)
        R = np.array(R)

        self.A = A
        self.B = B
        self.Q = Q
        self.R = R
        self.N = N
        self.setpoint = np.array(setpoint).flatten() # Ensure it's a 1D array
        self.output = 0.0

        # Constraints
        self.u_min = u_min
        self.u_max = u_max
        self.x_min = x_min
        self.x_max = x_max

        # CVXPY problem setup
        self.x = cp.Variable((self.A.shape[0], N + 1))
        self.u = cp.Variable((self.B.shape[1], N))

        self.objective = 0
        self.constraints = []

        # Build the objective function and constraints over the horizon
        for k in range(N):
            # Cost function: sum of state error and control effort
            self.objective += cp.quad_form(self.x[:, k] - self.setpoint, self.Q) + cp.quad_form(self.u[:, k], self.R)

            # System dynamics constraint
            self.constraints += [self.x[:, k+1] == self.A @ self.x[:, k] + self.B @ self.u[:, k]]

            # Input constraints
            if self.u_min is not None:
                self.constraints += [self.u[:, k] >= self.u_min]
            if self.u_max is not None:
                self.constraints += [self.u[:, k] <= self.u_max]

            # State constraints
            if self.x_min is not None:
                self.constraints += [self.x[:, k] >= self.x_min]
            if self.x_max is not None:
                self.constraints += [self.x[:, k] <= self.x_max]

        # Add terminal cost
        self.objective += cp.quad_form(self.x[:, self.N] - self.setpoint, self.Q)

        # Initial state constraint will be set in the calculate method
        self.x0 = cp.Parameter(A.shape[0])
        self.constraints += [self.x[:, 0] == self.x0]

        # Define the optimization problem
        self.problem = cp.Problem(cp.Minimize(self.objective), self.constraints)

        print("MPC Controller initialized successfully.")

    def step(self, measured_value, dt=None, **kwargs):
        """
        Calculates the optimal control output.

        Args:
            measured_value (float): The current measured state value.
            dt (float, optional): The time step (not used in this MPC version but kept for API consistency).

        Returns:
            float: The first optimal control input.
        """
        # Set the initial state parameter
        self.x0.value = np.array([measured_value]).flatten()

        # Solve the optimization problem
        try:
            self.problem.solve(solver=cp.OSQP, warm_start=True)

            if self.problem.status in ["infeasible", "unbounded"]:
                print(f"Warning: MPC problem is {self.problem.status}. Returning zero control.")
                self.output = 0.0
                return 0.0

            # Return the first control action in the optimal sequence
            self.output = self.u.value[0, 0]
            return self.output
        except Exception as e:
            print(f"Error during MPC solve: {e}. Returning zero control.")
            self.output = 0.0
            return 0.0

    def get_state(self):
        return {
            "output": self.output
            # The internal states of the MPC (like the optimal sequence x, u)
            # are complex and not easily summarized as a simple state.
            # We return the primary output for logging and connection purposes.
        }
