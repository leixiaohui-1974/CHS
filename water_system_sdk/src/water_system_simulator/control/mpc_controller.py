import cvxpy as cp
import numpy as np
from .base_controller import BaseController
from typing import List, Dict, Any, Optional
from ..data_processing.processors import (
    BaseDataProcessor, DataCleaner, InverseDistanceWeightingInterpolator,
    ThiessenPolygonInterpolator, KrigingInterpolator, UnitConverter, TimeResampler
)

# A factory to map processor types from config to their classes
PROCESSOR_FACTORY: Dict[str, Any] = {
    "DataCleaner": DataCleaner,
    "InverseDistanceWeightingInterpolator": InverseDistanceWeightingInterpolator,
    "ThiessenPolygonInterpolator": ThiessenPolygonInterpolator,
    "KrigingInterpolator": KrigingInterpolator,
    "UnitConverter": UnitConverter,
    "TimeResampler": TimeResampler,
}


class MPCController(BaseController):
    """
    A Model Predictive Control (MPC) controller for linear time-invariant (LTI) systems.
    Now with an optional data processing pipeline for the measured input.
    """
    def __init__(self, A, B, Q, R, N, setpoint, u_min=None, u_max=None, x_min=None, x_max=None,
                 data_pipeline: Optional[List[Dict[str, Any]]] = None, **kwargs):
        """
        Initializes the MPC controller.

        Args:
            A (np.ndarray): The state transition matrix.
            B (np.ndarray): The input matrix.
            Q (np.ndarray): The state weighting matrix.
            R (np.ndarray): The input weighting matrix.
            N (int): The prediction horizon.
            setpoint (np.ndarray): The desired state setpoint (reference).
            u_min (float, optional): Minimum control input.
            u_max (float, optional): Maximum control input.
            x_min (float, optional): Minimum state value.
            x_max (float, optional): Maximum state value.
            data_pipeline (Optional[List[Dict]]): Configuration for the data processing pipeline.
        """
        super().__init__(**kwargs)
        A, B, Q, R = np.array(A), np.array(B), np.array(Q), np.array(R)

        self.A, self.B, self.Q, self.R, self.N = A, B, Q, R, N
        self.setpoint = np.array(setpoint).flatten()
        self.output = 0.0

        self.u_min, self.u_max, self.x_min, self.x_max = u_min, u_max, x_min, x_max

        # --- CVXPY Problem Setup ---
        self.x = cp.Variable((A.shape[0], N + 1))
        self.u = cp.Variable((B.shape[1], N))
        self.objective = sum(cp.quad_form(self.x[:, k] - self.setpoint, Q) + cp.quad_form(self.u[:, k], R) for k in range(N))
        self.objective += cp.quad_form(self.x[:, N] - self.setpoint, Q)

        self.constraints = []
        for k in range(N):
            self.constraints += [self.x[:, k+1] == A @ self.x[:, k] + B @ self.u[:, k]]
            if u_min is not None: self.constraints += [self.u[:, k] >= u_min]
            if u_max is not None: self.constraints += [self.u[:, k] <= u_max]
            if x_min is not None: self.constraints += [self.x[:, k] >= x_min]
            if x_max is not None: self.constraints += [self.x[:, k] <= x_max]

        self.x0 = cp.Parameter(A.shape[0])
        self.constraints += [self.x[:, 0] == self.x0]
        self.problem = cp.Problem(cp.Minimize(self.objective), self.constraints)

        # --- Data Pipeline Setup ---
        self.data_pipeline: List[BaseDataProcessor] = []
        if data_pipeline:
            for step_config in data_pipeline:
                step_type = step_config.get("type")
                step_params = step_config.get("params", {})
                if step_type in PROCESSOR_FACTORY:
                    processor_class = PROCESSOR_FACTORY[step_type]
                    step_params['id'] = step_params.get('id', step_type)
                    self.data_pipeline.append(processor_class(**step_params))
                else:
                    raise ValueError(f"Unknown data processor type: {step_type}")

        print("MPC Controller initialized successfully.")

    def _execute_pipeline(self, raw_data: Any) -> Any:
        processed_data = raw_data
        for processor in self.data_pipeline:
            processed_data = processor.process(processed_data)
        return processed_data

    def step(self, raw_measured_value, dt=None, **kwargs):
        """
        Calculates the optimal control output after processing the raw measurement.

        Args:
            raw_measured_value (float): The current raw measured state value.
            dt (float, optional): Time step (for API consistency).

        Returns:
            float: The first optimal control input.
        """
        measured_value = self._execute_pipeline(raw_measured_value)
        self.x0.value = np.array([measured_value]).flatten()

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
        pipeline_state = {p.id: p.get_state() for p in self.data_pipeline}
        return {
            "output": self.output,
            "data_pipeline_state": pipeline_state
        }
