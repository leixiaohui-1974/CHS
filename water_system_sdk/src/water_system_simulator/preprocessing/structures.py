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
