from typing import Dict, Any, List
from scipy.optimize import minimize
import numpy as np

from .base_workflow import BaseWorkflow
from .utils.simulation_evaluator import evaluate_control_performance
from ..utils.logger import log

class ControlTuningWorkflow(BaseWorkflow):
    """
    A workflow for automatically tuning the parameters of a PID controller.
    """

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the control tuning workflow.

        Args:
            context: A dictionary containing the necessary inputs:
                - system_model (Dict): Configuration for the system agent.
                - optimization_objective (str): The metric to optimize (e.g., 'ISE').
                - parameter_bounds (List[tuple]): Bounds for each parameter (e.g., [(0, 10), (0, 5), (0, 1)]).
                - initial_guess (List[float]): Initial guess for the parameters [Kp, Ki, Kd].

        Returns:
            A dictionary containing the results of the optimization:
                - optimal_params (Dict): The best parameters found {'Kp': ..., 'Ki': ..., 'Kd': ...}.
                - final_cost (float): The final value of the objective function.
                - optimizer_result (OptimizeResult): The full result object from scipy.
        """
        log.info("Starting ControlTuningWorkflow...")

        # 1. Input Parsing
        try:
            system_model = context['system_model']
            objective = context['optimization_objective']
            bounds = context['parameter_bounds']
            initial_guess = context['initial_guess']
        except KeyError as e:
            log.error(f"Missing required key in context: {e}")
            raise

        # 2. Define the Objective Function for Scipy
        def objective_function(params: List[float]) -> float:
            """
            This function is called by the optimizer at each iteration.
            It takes a list of parameters, runs a simulation, and returns the cost.
            """
            kp, ki, kd = params
            controller_config = {'Kp': kp, 'Ki': ki, 'Kd': kd}

            log.debug(f"Evaluating parameters: Kp={kp:.4f}, Ki={ki:.4f}, Kd={kd:.4f}")

            cost = evaluate_control_performance(
                system_model=system_model,
                controller_config=controller_config,
                objective=objective
            )

            log.debug(f"Cost for current parameters: {cost:.4f}")
            return cost

        # 3. Call the Optimizer
        log.info("Starting optimization with scipy.optimize.minimize...")
        # Using 'L-BFGS-B' as it's a good choice for bounded problems.
        optimizer_result = minimize(
            fun=objective_function,
            x0=initial_guess,
            method='L-BFGS-B',
            bounds=bounds,
            options={'disp': True} # Display convergence messages
        )
        log.info("Optimization finished.")

        # 4. Result Encapsulation
        optimal_kp, optimal_ki, optimal_kd = optimizer_result.x
        final_cost = optimizer_result.fun

        result = {
            "optimal_params": {
                "Kp": optimal_kp,
                "Ki": optimal_ki,
                "Kd": optimal_kd
            },
            "final_cost": final_cost,
            "optimizer_result": optimizer_result
        }

        log.info(f"Optimal parameters found: {result['optimal_params']}")
        log.info(f"Final cost ({objective}): {final_cost}")

        return result
