import pandas as pd
from typing import Dict, Any

from chs_sdk.workflows.base_workflow import BaseWorkflow
from water_system_simulator.tools.identification_toolkit import IdentificationToolkit


class SystemIDWorkflow(BaseWorkflow):
    """
    A workflow for performing system identification on time-series data.
    """

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the system identification process.

        :param context: A dictionary expecting the following keys:
                        'data': A pandas DataFrame with 'inflow' and 'outflow' columns.
                        'model_type': The type of model to identify (e.g., 'Muskingum').
                        'dt': The time step of the data.
                        'initial_guess': A list of initial parameter guesses for the optimization.
                        'bounds': A list of tuples defining the bounds for each parameter.
        :return: A dictionary containing the identified model parameters and goodness-of-fit metrics.
        """
        # 1. Validate and extract data from the context
        if not all(k in context for k in ['data', 'model_type', 'dt', 'initial_guess', 'bounds']):
            raise ValueError("Context for SystemIDWorkflow is missing required keys.")

        data: pd.DataFrame = context['data']
        model_type: str = context['model_type']
        dt: float = context['dt']
        initial_guess: list = context['initial_guess']
        bounds: list = context['bounds']

        if not isinstance(data, pd.DataFrame) or not all(col in data.columns for col in ['inflow', 'outflow']):
            raise TypeError("'data' must be a pandas DataFrame with 'inflow' and 'outflow' columns.")

        # 2. Instantiate the toolkit
        toolkit = IdentificationToolkit()

        # 3. Perform the identification
        try:
            result = toolkit.identify_offline(
                model_type=model_type,
                inflow=data['inflow'].to_numpy(),
                outflow=data['outflow'].to_numpy(),
                dt=dt,
                initial_guess=initial_guess,
                bounds=bounds
            )
        except RuntimeError as e:
            # Handle potential errors from the identification process
            return {"error": str(e)}

        # 4. Return the results
        return {
            "status": "success",
            "identified_parameters": result.get("params"),
            "goodness_of_fit": {
                "rmse": result.get("rmse")
            }
        }
