# water_system_sdk/src/water_system_simulator/external_data/agents.py
import pandas as pd
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from typing import Dict, Any

class BaseExternalDataAgent(BaseModel, ABC):
    """
    Base class for all external data agents.
    Its core responsibility is to provide access to raw, unprocessed time-series data
    from an external source (e.g., CSV file, database, MQTT stream).
    """
    id: str

    class Config:
        arbitrary_types_allowed = True

    @abstractmethod
    def get_data(self, t: float) -> Dict[str, Any]:
        """
        Fetches data for the current simulation time.

        Args:
            t (float): The current simulation time.

        Returns:
            Dict[str, Any]: A dictionary containing the data for the given time.
                           The structure can vary depending on the data source.
        """
        pass

    def get_state(self) -> Dict[str, Any]:
        """
        Returns a dictionary representing the agent's current state.
        For passive data agents, this might be simple, e.g., the last data point read.
        """
        return {"id": self.id, "type": self.__class__.__name__}


class CsvDataAgent(BaseExternalDataAgent):
    """
    An external data agent that reads time-series data from a CSV file.
    The CSV file is expected to have a 'time' column that serves as the index.
    """
    file_path: str
    time_column: str = 'time'
    data: pd.DataFrame = Field(default_factory=pd.DataFrame, repr=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_data()

    def _load_data(self):
        """Loads data from the CSV file and sets the time index."""
        try:
            self.data = pd.read_csv(self.file_path)
            if self.time_column not in self.data.columns:
                raise ValueError(f"Time column '{self.time_column}' not found in {self.file_path}")
            self.data.set_index(self.time_column, inplace=True)
        except FileNotFoundError:
            # Handle error gracefully if file does not exist
            self.data = pd.DataFrame()
            print(f"Warning: CSV file not found at {self.file_path}")
        except Exception as e:
            self.data = pd.DataFrame()
            print(f"Error loading CSV data from {self.file_path}: {e}")

    def get_data(self, t: float) -> Dict[str, Any]:
        """
        Retrieves the row of data for the given time 't'.
        Uses nearest-neighbor lookup for simplicity.
        """
        if self.data.empty:
            return {}

        # Find the integer position of the index closest to the current time t
        nearest_position = self.data.index.get_indexer([t], method='nearest')[0]
        data_series = self.data.iloc[nearest_position]

        return data_series.to_dict()

    def get_state(self) -> Dict[str, Any]:
        """Returns the current state of the agent."""
        state = super().get_state()
        state.update({
            "file_path": self.file_path,
            "time_column": self.time_column,
            "loaded": not self.data.empty
        })
        return state
