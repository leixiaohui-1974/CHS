from dataclasses import dataclass
from typing import Tuple
import pandas as pd

@dataclass
class RainGauge:
    """
    Represents a single rain gauge station.

    Attributes:
        id (str): The unique identifier for the rain gauge.
        coords (Tuple[float, float]): The (x, y) coordinates of the gauge.
        time_series (pd.DataFrame): A pandas DataFrame containing the rainfall data.
                                    The index should be a DatetimeIndex, and it
                                    should have a single column named 'precipitation'.
    """
    id: str
    coords: Tuple[float, float]
    time_series: pd.DataFrame
