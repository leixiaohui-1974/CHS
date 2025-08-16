import numpy as np

def identify_time_constant(storage_data: np.ndarray, inflow_data: np.ndarray, dt: float) -> float:
    """
    Identifies the time constant (T) of a FirstOrderInertiaModel using batch least squares.

    The model is: storage(k+1) = A*storage(k) + B*inflow(k)
    where A = (1 - dt/T) and B = dt.

    This can be rewritten as:
    storage(k+1) - storage(k) = (-dt/T)*storage(k) + dt*inflow(k)

    Let y = storage(k+1) - storage(k)
    Let x = [-dt*storage(k), dt*inflow(k)]
    Let p = [1/T, 1] (parameters to be identified)

    y = x @ p
    We will identify p using least squares: p = (X.T @ X)^-1 @ X.T @ Y

    Args:
        storage_data (np.ndarray): A time series of storage values.
        inflow_data (np.ndarray): A time series of inflow values.
        dt (float): The time step of the data.

    Returns:
        float: The identified time constant (T).
    """
    if len(storage_data) != len(inflow_data):
        raise ValueError("Storage and inflow data must have the same length.")

    if len(storage_data) < 2:
        raise ValueError("At least two data points are required for identification.")

    # Prepare the Y vector and X matrix
    Y = storage_data[1:] - storage_data[:-1]

    # Reshape storage_data to be a column vector for the matrix
    storage_col = -dt * storage_data[:-1].reshape(-1, 1)
    inflow_col = dt * inflow_data[:-1].reshape(-1, 1)

    X = np.hstack([storage_col, inflow_col])

    # Solve for parameters p using the pseudo-inverse
    try:
        p = np.linalg.pinv(X.T @ X) @ X.T @ Y
    except np.linalg.LinAlgError:
        raise RuntimeError("Could not solve the least squares problem. The data may be linearly dependent.")

    # Extract 1/T from the parameters
    one_over_T = p[0]

    if one_over_T <= 0:
        raise ValueError("Identification resulted in a non-positive time constant, which is physically impossible.")

    time_constant = 1 / one_over_T

    return float(time_constant)
