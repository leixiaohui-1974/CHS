import pandas as pd
from abc import abstractmethod
from chs_sdk.modeling.base_model import BaseModel

class BaseExternalDataAgent(BaseModel):
    """
    Abstract base class for agents that provide data from external sources.
    """
    def __init__(self, **kwargs):
        super().__init__()
        self.output = None

    @abstractmethod
    def step(self, t, dt):
        """
        Represents a single time step of the agent's execution.

        This method should update the agent's output with data corresponding
        to the current simulation time.

        Args:
            t (float): The current simulation time.
            dt (float): The simulation time step.
        """
        pass

    @abstractmethod
    def get_state(self):
        """
        Returns a dictionary of the agent's current state.
        """
        pass


class CsvDataAgent(BaseExternalDataAgent):
    """
    An external data agent that reads time series data from a CSV file.
    """
    def __init__(self, filepath: str, time_column: str = None, **kwargs):
        """
        Initializes the CsvDataAgent.

        Args:
            filepath (str): The path to the CSV file.
            time_column (str, optional): The name of the column to be used as
                                         the time index. If None, assumes the
                                         first column is the index. Defaults to None.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        try:
            if time_column:
                self.data = pd.read_csv(filepath, index_col=time_column, parse_dates=True)
            else:
                self.data = pd.read_csv(filepath, index_col=0, parse_dates=True)
        except FileNotFoundError:
            raise FileNotFoundError(f"Could not find the specified data file: {filepath}")
        except Exception as e:
            raise IOError(f"Error reading or parsing CSV file at {filepath}: {e}")

        self.current_step = 0
        # Let's assume the simulation time 't' maps to the row number for simplicity,
        # as seen in other agents. A more robust implementation might interpolate
        # based on the actual timestamp.

    def step(self, t, dt):
        """
        Updates the agent's output with the data from the current row of the CSV.
        The output is a pandas Series containing all columns for the current timestep.
        """
        if self.current_step < len(self.data):
            self.output = self.data.iloc[self.current_step]
        else:
            # When data runs out, hold the last value. This is a common requirement.
            if not self.data.empty:
                self.output = self.data.iloc[-1]
            else:
                self.output = None

        self.current_step += 1

    def get_state(self):
        """Returns the current state of the agent."""
        return {
            "type": "CsvDataAgent",
            "current_step": self.current_step,
            "output": self.output.to_dict() if self.output is not None else None
        }
