import pandas as pd
import numpy as np

class RainfallModel:
    """
    Represents a simple rainfall model that can be initialized from a list or a CSV file.
    """
    def __init__(self, rainfall_pattern=None, rainfall_file=None, column_name='inflow'):
        """
        Initializes the rainfall model.

        Args:
            rainfall_pattern (list or np.ndarray, optional): A time series of rainfall values.
            rainfall_file (str, optional): Path to a CSV file containing rainfall data.
            column_name (str, optional): The name of the column to read from the CSV file.
        """
        if rainfall_file:
            try:
                df = pd.read_csv(rainfall_file)
                self.rainfall_pattern = df[column_name].tolist()
            except (FileNotFoundError, KeyError) as e:
                print(f"Error initializing RainfallModel from file: {e}")
                self.rainfall_pattern = []
        elif rainfall_pattern is not None:
            self.rainfall_pattern = rainfall_pattern
        else:
            raise ValueError("Either rainfall_pattern or rainfall_file must be provided.")

        self.time_step = 0

    def get_rainfall(self, t):
        """
        Gets the rainfall at a given time step. If t is beyond the pattern length,
        it holds the last value, ensuring a constant disturbance if needed.
        """
        if not self.rainfall_pattern:
            return 0.0
        if t < len(self.rainfall_pattern):
            return self.rainfall_pattern[t]
        else:
            # Hold the last value if the simulation runs longer than the pattern
            return self.rainfall_pattern[-1]

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
