import numpy as np

class RK4Integrator:
    """
    A fourth-order Runge-Kutta (RK4) integrator for solving ODEs.
    """
    def __init__(self, f, dt):
        """
        Initializes the RK4 integrator.

        Args:
            f (function): The function that defines the ODE, dy/dt = f(t, y).
            dt (float): The time step.
        """
        self.f = f
        self.dt = dt

    def step(self, t, y):
        """
        Performs a single integration step using the RK4 method.

        Args:
            t (float): The current time.
            y (np.ndarray): The current state vector.

        Returns:
            np.ndarray: The next state vector.
        """
        k1 = self.dt * self.f(t, y)
        k2 = self.dt * self.f(t + 0.5 * self.dt, y + 0.5 * k1)
        k3 = self.dt * self.f(t + 0.5 * self.dt, y + 0.5 * k2)
        k4 = self.dt * self.f(t + self.dt, y + k3)

        y_next = y + (k1 + 2*k2 + 2*k3 + k4) / 6.0
        return y_next
