import numpy as np
import pandas as pd

def _run_muskingum_simulation(inflow_series: np.ndarray, K: float, x: float, dt: float, initial_outflow: float, initial_inflow: float) -> np.ndarray:
    """Runs a Muskingum model simulation."""
    outflow = np.zeros_like(inflow_series, dtype=np.float64)
    if len(inflow_series) == 0:
        return outflow

    C1 = (dt - 2 * K * x) / (2 * K * (1 - x) + dt) if (2 * K * (1 - x) + dt) != 0 else 0
    C2 = (dt + 2 * K * x) / (2 * K * (1 - x) + dt) if (2 * K * (1 - x) + dt) != 0 else 0
    C3 = (2 * K * (1 - x) - dt) / (2 * K * (1 - x) + dt) if (2 * K * (1 - x) + dt) != 0 else 0

    I_prev = initial_inflow
    O_prev = initial_outflow

    for i in range(len(inflow_series)):
        I_t = inflow_series[i]
        O_t = C1 * I_t + C2 * I_prev + C3 * O_prev
        outflow[i] = max(0, O_t)
        O_prev = outflow[i]
        I_prev = I_t

    return outflow

def _run_integral_delay_simulation(inflow_change_series: np.ndarray, K: float, T: float, dt: float) -> np.ndarray:
    """Runs an Integral-Plus-Delay model simulation on the change in inflow."""
    outflow_change = np.zeros_like(inflow_change_series, dtype=np.float64)
    if len(inflow_change_series) == 0:
        return outflow_change

    delay_steps = int(T / dt)

    for i in range(1, len(inflow_change_series)):
        if i >= delay_steps:
             inflow_delayed = inflow_change_series[i - delay_steps]
             outflow_change[i] = outflow_change[i-1] + K * inflow_delayed * dt
        else:
            outflow_change[i] = outflow_change[i-1]

    return outflow_change

def run_single_model(inflow_series: np.ndarray, model_type: str, params: dict, dt: float, initial_inflow: float, initial_outflow: float) -> np.ndarray:
    """
    Runs a single simulation for a given model type and parameters.
    """
    if model_type == 'Muskingum':
        return _run_muskingum_simulation(inflow_series, K=params['K'], x=params['X'], dt=dt, initial_inflow=initial_inflow, initial_outflow=initial_outflow)
    elif model_type == 'IntegralDelay':
        inflow_change_series = inflow_series - initial_inflow
        outflow_change = _run_integral_delay_simulation(inflow_change_series, K=params['K'], T=params['T'], dt=dt)
        return initial_outflow + outflow_change
    else:
        raise ValueError(f"Unknown model type: {model_type}")

def run_piecewise_model(inflow_series: np.ndarray, model_bank: list, model_type: str, dt: float) -> np.ndarray:
    """
    Runs a piecewise simulation using a model bank.
    """
    outflow = np.zeros_like(inflow_series, dtype=np.float64)
    if len(inflow_series) == 0:
        return outflow

    initial_outflow = inflow_series[0]
    outflow[0] = initial_outflow

    # Sort model_bank by max_value to ensure correct parameter selection
    model_bank.sort(key=lambda x: x['max_value'])

    if model_type == 'Muskingum':
        I_prev = inflow_series[0]
        O_prev = initial_outflow

        for i in range(1, len(inflow_series)):
            I_t = inflow_series[i]

            # Find params for current inflow
            params = next((seg['parameters'] for seg in model_bank if I_t <= seg['max_value']), model_bank[-1]['parameters'])
            K = params['K']
            x = params['X']

            C1 = (dt - 2 * K * x) / (2 * K * (1 - x) + dt) if (2 * K * (1 - x) + dt) != 0 else 0
            C2 = (dt + 2 * K * x) / (2 * K * (1 - x) + dt) if (2 * K * (1 - x) + dt) != 0 else 0
            C3 = (2 * K * (1 - x) - dt) / (2 * K * (1 - x) + dt) if (2 * K * (1 - x) + dt) != 0 else 0

            O_t = C1 * I_t + C2 * I_prev + C3 * O_prev
            outflow[i] = max(0, O_t)

            O_prev = outflow[i]
            I_prev = I_t

    elif model_type == 'IntegralDelay':
         for i in range(1, len(inflow_series)):
            I_t = inflow_series[i]
            params = next((seg['parameters'] for seg in model_bank if I_t <= seg['max_value']), model_bank[-1]['parameters'])
            K = params['K']
            T = params['T']
            delay_steps = int(T / dt)

            if i > delay_steps:
                # For IntegralDelay, we integrate the change from the initial operating point.
                # This piecewise implementation is tricky because the "initial" point changes.
                # A simpler approach for piecewise IntegralDelay would be to assume it integrates the absolute inflow.
                # This is a deviation from the single-point identification model, but more practical for a piecewise model.
                inflow_delayed = inflow_series[i - delay_steps]
                outflow[i] = outflow[i-1] + K * inflow_delayed * dt
            else:
                outflow[i] = outflow[i-1]
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    return outflow
