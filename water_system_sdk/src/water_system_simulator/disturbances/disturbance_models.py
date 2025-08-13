class RainfallModel:
    """
    Represents a simple rainfall model.
    """
    def __init__(self, rainfall_pattern):
        """
        Initializes the rainfall model.

        Args:
            rainfall_pattern (list or np.ndarray): A time series of rainfall values.
        """
        self.rainfall_pattern = rainfall_pattern
        self.time_step = 0

    def get_rainfall(self, t):
        """
        Gets the rainfall at a given time.

        Args:
            t (int): The current time step.

        Returns:
            float: The rainfall at the current time step.
        """
        if t < len(self.rainfall_pattern):
            return self.rainfall_pattern[t]
        else:
            return 0.0 # No rainfall after the pattern ends

class WaterConsumptionModel:
    """
    Represents a simple water consumption model.
    """
    def __init__(self, consumption_pattern):
        """
        Initializes the water consumption model.

        Args:
            consumption_pattern (list or np.ndarray): A time series of water consumption values.
        """
        self.consumption_pattern = consumption_pattern
        self.time_step = 0

    def get_consumption(self, t):
        """
        Gets the water consumption at a given time.

        Args:
            t (int): The current time step.

        Returns:
            float: The water consumption at the current time step.
        """
        if t < len(self.consumption_pattern):
            return self.consumption_pattern[t]
        else:
            # Assume constant consumption after pattern ends
            return self.consumption_pattern[-1] if self.consumption_pattern else 0.0
