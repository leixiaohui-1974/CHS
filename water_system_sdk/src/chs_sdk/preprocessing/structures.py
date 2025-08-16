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
# This file will contain data structures for the preprocessing tools.
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import numpy as np

@dataclass
class SubBasinPreprocessing:
    """
    A data structure to hold preprocessing information for a single sub-basin.
    """
    id: str
    mask: np.ndarray
    area_sqkm: float = 0.0
    avg_slope: float = 0.0
    river_length_km: float = 0.0
    longest_flow_path_km: float = 0.0
    physical_parameters: Dict[str, Any] = field(default_factory=dict)
    model_parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParameterZonePreprocessing:
    """
    A data structure to hold preprocessing information for a single parameter zone.
    """
    id: str
    mask: np.ndarray
    sub_basins: List[SubBasinPreprocessing] = field(default_factory=list)
    observation_point: Optional[Any] = None # Could be coordinates or a station ID

