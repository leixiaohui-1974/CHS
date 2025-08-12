import numpy as np

class EulerIntegrator:
    """
    A simple Euler integrator for solving ordinary differential equations (ODEs).
    """
    def __init__(self, f, dt):
        """
        Initializes the Euler integrator.

        Args:
            f (function): The function that defines the ODE (dy/dt = f(t, y)).
            dt (float): The time step.
        """
        self.f = f
        self.dt = dt

    def step(self, t, y):
        """
        Performs a single integration step.

        Args:
            t (float): The current time.
            y (np.ndarray): The current state vector.

        Returns:
            np.ndarray: The next state vector.
        """
        return y + self.dt * self.f(t, y)
