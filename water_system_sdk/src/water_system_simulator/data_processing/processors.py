# water_system_sdk/src/water_system_simulator/data_processing/processors.py
import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class BaseDataProcessor(BaseModel, ABC):
    """
    Abstract base class for all data processing steps (strategies).

    Each processor takes data from the previous step (or raw data),
    performs a specific transformation, and returns the processed data.
    """
    id: str

    class Config:
        arbitrary_types_allowed = True

    @abstractmethod
    def process(self, data_input: Any) -> Any:
        """
        The core method for the processing strategy.

        Args:
            data_input: The data from the previous processing step or the raw input.
                        The type can vary (e.g., a single value, a dictionary, a DataFrame).

        Returns:
            The processed data, which will be passed to the next step in the pipeline.
        """
        pass

    def get_state(self) -> Dict[str, Any]:
        """
        Returns a dictionary representing the processor's current state.
        By default, it returns the processor's configuration.
        """
        return self.dict()

# --- Data Cleaning Processors ---

class DataCleaner(BaseDataProcessor):
    """
    A processor to perform basic data cleaning, such as handling missing values.
    """
    strategy: str = 'fill' # e.g., 'fill', 'ffill', 'bfill', 'drop'
    fill_value: Optional[float] = 0.0

    def process(self, data_input: pd.DataFrame) -> pd.DataFrame:
        """
        Cleans the input DataFrame based on the configured strategy.

        Args:
            data_input: A pandas DataFrame.

        Returns:
            A cleaned pandas DataFrame.
        """
        if not isinstance(data_input, pd.DataFrame):
            # Or raise an error, depending on desired strictness
            return data_input

        if self.strategy == 'fill':
            return data_input.fillna(self.fill_value)
        elif self.strategy == 'ffill':
            return data_input.ffill()
        elif self.strategy == 'bfill':
            return data_input.bfill()
        elif self.strategy == 'drop':
            return data_input.dropna()
        else:
            return data_input

# --- Spatial Interpolation Processors ---

class InverseDistanceWeightingInterpolator(BaseDataProcessor):
    """
    Performs spatial interpolation using the Inverse Distance Weighting (IDW) method.
    It assumes the input data is from multiple stations with known locations.
    """
    station_locations: Dict[str, tuple] # e.g., {"station1": (lat, lon), ...}
    target_location: tuple # e.g., (lat, lon)
    power: float = 2.0

    def process(self, data_input: Dict[str, float]) -> float:
        """
        Interpolates a value at the target location from station data.

        Args:
            data_input: A dictionary where keys are station IDs (matching keys in
                        station_locations) and values are the measurements.

        Returns:
            The interpolated value at the target location.
        """
        numer = 0
        denom = 0
        for station_id, value in data_input.items():
            if station_id not in self.station_locations:
                continue

            station_loc = self.station_locations[station_id]
            dist_sq = (self.target_location[0] - station_loc[0])**2 + \
                      (self.target_location[1] - station_loc[1])**2

            if dist_sq == 0:
                return value # We are at the station, return its value directly

            weight = 1.0 / (dist_sq ** (self.power / 2.0))
            numer += weight * value
            denom += weight

        return numer / denom if denom > 0 else 0.0

class ThiessenPolygonInterpolator(BaseDataProcessor):
    """
    Placeholder for Thiessen Polygon Interpolator.
    This would typically involve pre-calculating polygon areas and weights.
    """
    def process(self, data_input: Any) -> Any:
        print("Warning: ThiessenPolygonInterpolator is a placeholder and has not been implemented.")
        return data_input

class KrigingInterpolator(BaseDataProcessor):
    """
    Placeholder for Kriging Interpolator.
    This would require a library like pykrige.
    """
    def process(self, data_input: Any) -> Any:
        print("Warning: KrigingInterpolator is a placeholder and has not been implemented.")
        return data_input

# --- Data Transformation Processors ---

class UnitConverter(BaseDataProcessor):
    """

    Converts a numerical value from a source unit to a target unit using a scaling factor.
    """
    factor: float # e.g., to convert mm to m, factor is 0.001

    def process(self, data_input: float) -> float:
        """
        Applies the conversion factor to the input data.
        """
        if not isinstance(data_input, (int, float)):
            return data_input # Or raise error
        return data_input * self.factor

class TimeResampler(BaseDataProcessor):
    """
    Resamples a time-series DataFrame to a different frequency.
    """
    rule: str # e.g., '1H' for hourly, '1D' for daily
    aggregation_method: str = 'mean' # e.g., 'mean', 'sum', 'first'

    def process(self, data_input: pd.DataFrame) -> pd.DataFrame:
        """
        Resamples the DataFrame. Assumes a DatetimeIndex.
        """
        if not isinstance(data_input, pd.DataFrame) or not isinstance(data_input.index, pd.DatetimeIndex):
            # Try to convert index if it's not already datetime
            try:
                data_input.index = pd.to_datetime(data_input.index)
            except (ValueError, TypeError):
                print("Warning: TimeResampler requires a DatetimeIndex.")
                return data_input

        return data_input.resample(self.rule).agg(self.aggregation_method)
