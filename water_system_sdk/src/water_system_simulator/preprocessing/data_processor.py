from abc import ABC, abstractmethod
from typing import List, Dict
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
from pykrige.ok import OrdinaryKriging
from water_system_simulator.preprocessing.structures import RainGauge


class BaseDataProcessor(ABC):
    """
    Abstract base class for all data processing components.
    """
    @abstractmethod
    def process(self, data_input: pd.DataFrame) -> pd.DataFrame:
        """
        Process the input data and return the processed data.

        Args:
            data_input (pd.DataFrame): The input data to process.

        Returns:
            pd.DataFrame: The processed data.
        """
        pass


class Pipeline(BaseDataProcessor):
    """
    A pipeline that chains multiple data processors together.
    """
    def __init__(self, processors: list):
        """
        Initializes the Pipeline.

        Args:
            processors (list): A list of data processor instances that inherit
                               from BaseDataProcessor.
        """
        self.processors = processors

    def process(self, data_input: pd.DataFrame) -> pd.DataFrame:
        """
        Processes the data by passing it through each processor in the pipeline.
        """
        data = data_input
        for processor in self.processors:
            data = processor.process(data)
        return data


class DataCleaner(BaseDataProcessor):
    """
    A data processor to clean data, e.g., by filling missing values.
    """
    def __init__(self, strategy: str = 'ffill', value=None):
        """
        Initializes the DataCleaner.

        Args:
            strategy (str): The strategy for filling missing values.
                            Options: 'ffill', 'bfill', 'mean', 'median', 'constant'.
            value (scalar, optional): The value to use when strategy is 'constant'.
        """
        self.strategy = strategy
        self.value = value

    def process(self, data_input: pd.DataFrame) -> pd.DataFrame:
        """
        Fills missing values in the DataFrame.
        """
        if self.strategy == 'ffill':
            return data_input.ffill()
        elif self.strategy == 'bfill':
            return data_input.bfill()
        elif self.strategy == 'mean':
            return data_input.fillna(data_input.mean())
        elif self.strategy == 'median':
            return data_input.fillna(data_input.median())
        elif self.strategy == 'constant':
            return data_input.fillna(self.value)
        else:
            raise ValueError(f"Unknown cleaning strategy: {self.strategy}")


class UnitConverter(BaseDataProcessor):
    """
    A data processor to convert units by applying a scaling factor.
    """
    def __init__(self, scale_factor: float, columns: list = None):
        """
        Initializes the UnitConverter.

        Args:
            scale_factor (float): The factor to multiply the data by.
            columns (list, optional): A list of column names to apply the
                                      conversion to. If None, applies to all
                                      numeric columns. Defaults to None.
        """
        self.scale_factor = scale_factor
        self.columns = columns

    def process(self, data_input: pd.DataFrame) -> pd.DataFrame:
        """
        Applies the unit conversion.
        """
        data = data_input.copy()
        if self.columns:
            for col in self.columns:
                if col in data.columns and pd.api.types.is_numeric_dtype(data[col]):
                    data[col] = data[col] * self.scale_factor
        else:
            for col in data.columns:
                if pd.api.types.is_numeric_dtype(data[col]):
                    data[col] = data[col] * self.scale_factor
        return data


class TimeResampler(BaseDataProcessor):
    """
    A data processor to resample time series data to a different frequency.
    """
    def __init__(self, rule: str, agg_func: str = 'mean'):
        """
        Initializes the TimeResampler.

        Args:
            rule (str): The new frequency (e.g., 'D' for daily, 'H' for hourly).
                        See pandas documentation for frequency strings.
            agg_func (str): The aggregation function to use (e.g., 'mean', 'sum').
        """
        self.rule = rule
        self.agg_func = agg_func

    def process(self, data_input: pd.DataFrame) -> pd.DataFrame:
        """
        Resamples the time series data.
        """
        if not isinstance(data_input.index, pd.DatetimeIndex):
            raise TypeError("TimeResampler requires a DatetimeIndex.")
        return data_input.resample(self.rule).agg(self.agg_func)


# --- Spatial Interpolators ---

class ThiessenPolygonInterpolator(BaseDataProcessor):
    """
    Interpolates spatial data using the Thiessen Polygon (Nearest Neighbor) method.
    Each target location is assigned the value of the nearest data point (gauge).
    """
    def __init__(self, rain_gauges: List[RainGauge], target_locations: Dict[str, tuple]):
        """
        Initializes the ThiessenPolygonInterpolator.

        Args:
            rain_gauges (List[RainGauge]): A list of RainGauge objects, which
                                           contain coordinates and IDs.
            target_locations (Dict[str, tuple]): A dictionary where keys are the
                                                 identifiers of the target locations
                                                 and values are their (x, y) coordinates.
        """
        if not rain_gauges:
            raise ValueError("Rain gauges list cannot be empty.")

        self.gauge_ids = [g.id for g in rain_gauges]
        self.target_ids = list(target_locations.keys())

        gauge_coords = np.array([g.coords for g in rain_gauges])
        target_coords = np.array(list(target_locations.values()))

        # Use cKDTree for efficient nearest neighbor lookup and store the indices
        kdtree = cKDTree(gauge_coords)
        _, self.nearest_indices = kdtree.query(target_coords, k=1)

    def process(self, data_input: pd.DataFrame) -> pd.DataFrame:
        """
        Assigns the time series of the nearest gauge to each target location.

        Args:
            data_input (pd.DataFrame): A DataFrame where the index is time and
                                       columns are gauge identifiers.

        Returns:
            pd.DataFrame: A DataFrame with interpolated values for target locations.
        """
        if not all(gid in data_input.columns for gid in self.gauge_ids):
            raise ValueError("Input DataFrame must contain columns for all rain gauges.")

        result_df = pd.DataFrame(index=data_input.index, columns=self.target_ids)
        for i, target_id in enumerate(self.target_ids):
            nearest_gauge_id = self.gauge_ids[self.nearest_indices[i]]
            result_df[target_id] = data_input[nearest_gauge_id]

        return result_df


class InverseDistanceWeightingInterpolator(BaseDataProcessor):
    """
    Interpolates spatial data using the Inverse Distance Weighting (IDW) method.
    """
    def __init__(self, rain_gauges: List[RainGauge], target_locations: Dict[str, tuple], power: float = 2.0):
        """
        Initializes the IDW interpolator.

        Args:
            rain_gauges (List[RainGauge]): A list of RainGauge objects.
            target_locations (Dict[str, tuple]): A dictionary of target locations.
            power (float): The power parameter (p) for weighting. Defaults to 2.0.
        """
        if power <= 0:
            raise ValueError("Power parameter must be greater than zero.")
        if not rain_gauges:
            raise ValueError("Rain gauges list cannot be empty.")

        self.power = power
        self.rain_gauges = rain_gauges
        self.gauge_ids = [g.id for g in rain_gauges]
        self.target_locations = target_locations
        self.target_ids = list(target_locations.keys())

        # Pre-calculate weights to avoid doing it on every process call
        gauge_coords = np.array([g.coords for g in self.rain_gauges])
        target_coords = np.array(list(self.target_locations.values()))

        distances = np.linalg.norm(target_coords[:, np.newaxis, :] - gauge_coords, axis=2)
        self.zero_dist_mask = (distances == 0)

        with np.errstate(divide='ignore', invalid='ignore'):
            weights = 1.0 / (distances ** self.power)
        weights[np.isinf(weights)] = 0  # Handle division by zero
        weights[np.isnan(weights)] = 0  # Handle invalid values if any

        sum_of_weights = np.sum(weights, axis=1, keepdims=True)
        # Avoid division by zero if a target is equidistant from all gauges (or all are at infinity)
        self.normalized_weights = np.divide(weights, sum_of_weights, where=sum_of_weights!=0)


    def process(self, data_input: pd.DataFrame) -> pd.DataFrame:
        """
        Performs IDW interpolation on the input data.

        Args:
            data_input (pd.DataFrame): DataFrame with gauge data.

        Returns:
            pd.DataFrame: DataFrame with interpolated data for target locations.
        """
        if not all(gid in data_input.columns for gid in self.gauge_ids):
            raise ValueError("Input DataFrame must contain columns for all rain gauges.")

        rainfall_values = data_input[self.gauge_ids].values
        interpolated_values = np.dot(rainfall_values, self.normalized_weights.T)
        result_df = pd.DataFrame(interpolated_values, index=data_input.index, columns=self.target_ids)

        # Handle cases where a target location is exactly on a gauge
        if np.any(self.zero_dist_mask):
            target_indices, gauge_indices = np.where(self.zero_dist_mask)
            for t_idx, g_idx in zip(target_indices, gauge_indices):
                target_id = self.target_ids[t_idx]
                gauge_id = self.gauge_ids[g_idx]
                result_df[target_id] = data_input[gauge_id]

        return result_df


class KrigingInterpolator(BaseDataProcessor):
    """
    Interpolates spatial data using Ordinary Kriging.
    This method is computationally intensive as it fits a model for each time step.
    """
    def __init__(self, rain_gauges: List[RainGauge], target_locations: Dict[str, tuple], variogram_model='linear', verbose=False, enable_plotting=False):
        """
        Initializes the Kriging interpolator.
        """
        if not rain_gauges:
            raise ValueError("Rain gauges list cannot be empty.")

        self.rain_gauges = rain_gauges
        self.gauge_ids = [g.id for g in rain_gauges]
        self.target_locations = target_locations
        self.target_ids = list(target_locations.keys())
        self.variogram_model = variogram_model
        self.verbose = verbose
        self.enable_plotting = enable_plotting

        self.gauge_coords = np.array([g.coords for g in self.rain_gauges])
        self.target_coords = np.array(list(self.target_locations.values()))

    def process(self, data_input: pd.DataFrame) -> pd.DataFrame:
        """
        Performs Kriging interpolation for each time step in the input data.
        """
        if not all(gid in data_input.columns for gid in self.gauge_ids):
            raise ValueError("Input DataFrame must contain columns for all rain gauges.")

        gauge_x = self.gauge_coords[:, 0]
        gauge_y = self.gauge_coords[:, 1]
        target_x = self.target_coords[:, 0]
        target_y = self.target_coords[:, 1]

        interpolated_results = []
        for timestamp, series in data_input[self.gauge_ids].iterrows():
            rainfall_values = series.values

            if np.all(np.isnan(rainfall_values)) or len(set(rainfall_values)) <= 1:
                interpolated_step = np.full(len(self.target_ids), rainfall_values[0])
            else:
                try:
                    ok = OrdinaryKriging(
                        gauge_x, gauge_y, rainfall_values,
                        variogram_model=self.variogram_model,
                        verbose=self.verbose, enable_plotting=self.enable_plotting,
                    )
                    k_values, _ = ok.execute('points', target_x, target_y)
                    interpolated_step = k_values
                except Exception as e:
                    print(f"Warning: Kriging failed for timestamp {timestamp}. Falling back to mean. Error: {e}")
                    interpolated_step = np.full(len(self.target_ids), np.nanmean(rainfall_values))

            interpolated_results.append(interpolated_step)

        result_df = pd.DataFrame(
            interpolated_results,
            index=data_input.index,
            columns=self.target_ids
        )
        return result_df
