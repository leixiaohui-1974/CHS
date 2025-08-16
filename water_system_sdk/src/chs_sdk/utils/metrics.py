import numpy as np

def calculate_nse(simulated: np.ndarray, observed: np.ndarray) -> float:
    """Calculates the Nash-Sutcliffe Efficiency."""
    if len(simulated) != len(observed):
        raise ValueError("Simulated and observed arrays must have the same length.")
    if np.var(observed) == 0:
        return -np.inf # Or handle as an error, as NSE is undefined.
    return 1 - (np.sum((simulated - observed)**2) / np.sum((observed - np.mean(observed))**2))

def calculate_rmse(simulated: np.ndarray, observed: np.ndarray) -> float:
    """Calculates the Root Mean Squared Error."""
    if len(simulated) != len(observed):
        raise ValueError("Simulated and observed arrays must have the same length.")
    return np.sqrt(np.mean((simulated - observed)**2))
