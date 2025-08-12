import numpy as np

class IntegralDelayModel:
    """
    Represents a storage object with integral and delay characteristics.
    This model is a simple representation of a river or channel reach.
    """
    def __init__(self, initial_outflow, delay_steps):
        """
        Initializes the integral delay model.

        Args:
            initial_outflow (float): The initial outflow from the object.
            delay_steps (int): The number of time steps for the delay.
        """
        self.outflow = initial_outflow
        self.delay_steps = delay_steps
        self.inflow_history = np.zeros(delay_steps)

    def step(self, inflow):
        """
        Performs a single simulation step.

        Args:
            inflow (float): The inflow to the object at the current time step.

        Returns:
            float: The outflow from the object at the current time step.
        """
        delayed_inflow = self.inflow_history[0]
        self.inflow_history = np.roll(self.inflow_history, -1)
        self.inflow_history[-1] = inflow

        # In this simple model, outflow is equal to the delayed inflow.
        # A more complex model could include storage effects.
        self.outflow = delayed_inflow
        return self.outflow

class FirstOrderInertiaModel:
    """
    Represents a storage object with first-order inertia characteristics.
    This model can represent a reservoir or a lake.
    """
    def __init__(self, initial_storage, time_constant):
        """
        Initializes the first-order inertia model.

        Args:
            initial_storage (float): The initial storage of the object.
            time_constant (float): The time constant of the model (T).
        """
        self.storage = initial_storage
        self.time_constant = time_constant

    def step(self, inflow):
        """
        Performs a single simulation step.

        Args:
            inflow (float): The inflow to the object at the current time step.

        Returns:
            float: The outflow from the object at the current time step.
        """
        # The outflow is proportional to the storage.
        outflow = self.storage / self.time_constant

        # Update storage based on inflow and outflow.
        d_storage_dt = inflow - outflow
        self.storage += d_storage_dt

        return outflow
