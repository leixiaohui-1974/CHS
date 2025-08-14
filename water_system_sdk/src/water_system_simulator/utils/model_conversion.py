import numpy as np

def integral_delay_to_ss(K: float, T: float, dt: float) -> tuple[np.ndarray, np.ndarray]:
    """
    Converts an Integral-Plus-Delay model into a discrete state-space representation.

    The model is described by: dy/dt = K * u(t-T)
    This is discretized as: y(k+1) = y(k) + K * dt * u(k-d)
    where d = T / dt is the delay in time steps.

    To represent this in state-space form x(k+1) = A*x(k) + B*u(k), we augment
    the state to include the history of inputs.
    The state is defined as:
    x(k) = [y(k), u(k-1), u(k-2), ..., u(k-d)]^T
    The state size is n = d + 1.

    The input is u(k).

    The state update equations are:
    y(k+1)      = y(k) + K*dt * u(k-d)
    u_new(k-1)  = u(k)
    u_new(k-2)  = u(k-1)
    ...
    u_new(k-d)  = u(k-d+1)

    Args:
        K (float): The integral gain.
        T (float): The time delay.
        dt (float): The time step.

    Returns:
        tuple[np.ndarray, np.ndarray]: A tuple containing the A and B matrices.
    """
    if dt <= 0:
        raise ValueError("dt must be positive.")
    if T < 0:
        raise ValueError("Time delay T cannot be negative.")

    delay_steps = int(round(T / dt))

    # Handle the no-delay case separately for clarity
    if delay_steps == 0:
        A = np.array([[1.0]])
        B = np.array([[K * dt]])
        return A, B

    n = delay_steps + 1  # State dimension

    # Initialize A and B matrices with zeros
    A = np.zeros((n, n))
    B = np.zeros((n, 1))

    # State update for y(k):
    # y(k+1) = 1*y(k) + (K*dt)*u(k-d)
    # The state for y is x[0], and for u(k-d) is x[delay_steps]
    A[0, 0] = 1.0
    A[0, delay_steps] = K * dt

    # State update for the delayed inputs (a shift register):
    # The new u(k-1) is the current input u(k)
    B[1, 0] = 1.0
    # The new u(k-2) was the old u(k-1), etc.
    # x_new[2] = x_old[1], x_new[3] = x_old[2], ..., x_new[d] = x_old[d-1]
    for i in range(2, n):
        A[i, i - 1] = 1.0

    return A, B
