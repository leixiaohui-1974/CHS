import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple

from .structures import RainGauge

class BaseSpatialInterpolator(ABC):
    """
    Abstract base class for spatial interpolation strategies.
    """
    @abstractmethod
    def interpolate(self, rain_gauges: List[RainGauge], target_locations: Dict[str, Tuple[float, float]]) -> pd.DataFrame:
        """
        Interpolates rainfall data from a list of rain gauges to a set of target locations.

        Args:
            rain_gauges (List[RainGauge]): A list of rain gauge objects, each
                                           containing coordinates and time series data.
            target_locations (Dict[str, Tuple[float, float]]): A dictionary mapping
                                                               target location IDs to
                                                               their (x, y) coordinates.

        Returns:
            pd.DataFrame: A DataFrame where the index is the timestamp and each
                          column corresponds to a target location ID, containing the
                          interpolated rainfall values.
        """
        pass


class InverseDistanceWeightingInterpolator(BaseSpatialInterpolator):
    """
    Interpolates rainfall data using the Inverse Distance Weighting (IDW) method.
    """
    def __init__(self, power: int = 2):
        """
        Initializes the IDW interpolator.

        Args:
            power (int): The power parameter (p) for the IDW calculation. Higher
                         values give more influence to closer points.
        """
        if power <= 0:
            raise ValueError("Power parameter must be greater than zero.")
        self.power = power

    def interpolate(self, rain_gauges: List[RainGauge], target_locations: Dict[str, Tuple[float, float]]) -> pd.DataFrame:
        if not rain_gauges:
            raise ValueError("Rain gauge list cannot be empty.")

        # Assume all gauges have the same time index. Use the first gauge's index.
        time_index = rain_gauges[0].time_series.index
        results = pd.DataFrame(index=time_index, columns=list(target_locations.keys()), dtype=float)

        gauge_coords = np.array([g.coords for g in rain_gauges])

        for timestamp in time_index:
            # Get the rainfall value from each gauge at the current timestamp
            gauge_values = np.array([g.time_series.loc[timestamp].iloc[0] for g in rain_gauges])

            for target_id, target_coord in target_locations.items():
                target_coord = np.array(target_coord)
                distances = np.linalg.norm(gauge_coords - target_coord, axis=1)

                # Handle case where a target point is exactly at a gauge location
                if np.any(distances < 1e-9):
                    interpolated_value = gauge_values[np.argmin(distances)]
                else:
                    weights = 1.0 / (distances ** self.power)
                    weighted_sum = np.sum(weights * gauge_values)
                    total_weight = np.sum(weights)
                    interpolated_value = weighted_sum / total_weight

                results.loc[timestamp, target_id] = interpolated_value

        return results
