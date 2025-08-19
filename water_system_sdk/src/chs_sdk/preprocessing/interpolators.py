from abc import ABC, abstractmethod
from typing import List, Dict
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
from pykrige.ok import OrdinaryKriging
from chs_sdk.preprocessing.structures import RainGauge


class BaseSpatialInterpolator(ABC):
    """
    Abstract base class for all spatial interpolation components.
    It defines a standard interface for different interpolation methods.
    """
    def _combine_gauge_data(self, rain_gauges: List[RainGauge]) -> pd.DataFrame:
        """
        A utility method to combine time series from multiple gauges into a
        single DataFrame. It assumes all gauges share the same DatetimeIndex.
        """
        if not rain_gauges:
            raise ValueError("Rain gauge list cannot be empty.")

        all_series = []
        for gauge in rain_gauges:
            # Extract the first data column as a pandas Series
            data_series = gauge.time_series.iloc[:, 0]
            # Set the name of the Series, which will be used as the column name
            data_series.name = gauge.id
            all_series.append(data_series)

        # Concatenate all named series into a single dataframe
        combined_df = pd.concat(all_series, axis=1)
        combined_df.sort_index(inplace=True)

        # Normalize the DatetimeIndex to a float index of seconds from the start
        if isinstance(combined_df.index, pd.DatetimeIndex):
            start_time = combined_df.index[0]
            combined_df.index = (combined_df.index - start_time).total_seconds()

        return combined_df

    @abstractmethod
    def interpolate(self, rain_gauges: List[RainGauge], target_locations: Dict[str, tuple]) -> pd.DataFrame:
        """
        Performs spatial interpolation from a set of source rain gauges to a
        set of target locations.

        Args:
            rain_gauges (List[RainGauge]): A list of RainGauge objects, each
                                           containing its ID, coordinates, and
                                           a time series of measurements.
            target_locations (Dict[str, tuple]): A dictionary where keys are the
                                                 identifiers of the target locations
                                                 (e.g., sub-basin centroids) and
                                                 values are their (x, y) coordinates.

        Returns:
            pd.DataFrame: A DataFrame where the index is time and columns are the
                          target location identifiers, containing the interpolated
                          rainfall values.
        """
        pass


class ThiessenPolygonInterpolator(BaseSpatialInterpolator):
    """
    Interpolates spatial data using the Thiessen Polygon (Nearest Neighbor) method.
    Each target location is assigned the value of the nearest data point (gauge).
    """
    def interpolate(self, rain_gauges: List[RainGauge], target_locations: Dict[str, tuple]) -> pd.DataFrame:
        if not rain_gauges:
            raise ValueError("Rain gauges list cannot be empty.")

        gauge_ids = [g.id for g in rain_gauges]
        target_ids = list(target_locations.keys())

        gauge_coords = np.array([g.coords for g in rain_gauges])
        target_coords = np.array(list(target_locations.values()))

        # Use cKDTree for efficient nearest neighbor lookup
        kdtree = cKDTree(gauge_coords)
        _, nearest_indices = kdtree.query(target_coords, k=1)

        # Combine gauge data into a single DataFrame
        data_input = self._combine_gauge_data(rain_gauges)

        result_df = pd.DataFrame(index=data_input.index, columns=target_ids)
        for i, target_id in enumerate(target_ids):
            nearest_gauge_id = gauge_ids[nearest_indices[i]]
            result_df[target_id] = data_input[nearest_gauge_id]

        return result_df


class InverseDistanceWeightingInterpolator(BaseSpatialInterpolator):
    """
    Interpolates spatial data using the Inverse Distance Weighting (IDW) method.
    """
    def __init__(self, power: float = 2.0):
        if power <= 0:
            raise ValueError("Power parameter must be greater than zero.")
        self.power = power

    def interpolate(self, rain_gauges: List[RainGauge], target_locations: Dict[str, tuple]) -> pd.DataFrame:
        if not rain_gauges:
            raise ValueError("Rain gauges list cannot be empty.")

        gauge_ids = [g.id for g in rain_gauges]
        target_ids = list(target_locations.keys())
        gauge_coords = np.array([g.coords for g in rain_gauges])
        target_coords = np.array(list(target_locations.values()))

        # Pre-calculate weights
        distances = np.linalg.norm(target_coords[:, np.newaxis, :] - gauge_coords, axis=2)
        zero_dist_mask = (distances == 0)

        with np.errstate(divide='ignore', invalid='ignore'):
            weights = 1.0 / (distances ** self.power)
        weights[np.isinf(weights)] = 0
        weights[np.isnan(weights)] = 0

        sum_of_weights = np.sum(weights, axis=1, keepdims=True)
        normalized_weights = np.divide(weights, sum_of_weights, where=sum_of_weights != 0)

        # Combine gauge data and perform interpolation
        data_input = self._combine_gauge_data(rain_gauges)
        rainfall_values = data_input[gauge_ids].values
        interpolated_values = np.dot(rainfall_values, normalized_weights.T)
        result_df = pd.DataFrame(interpolated_values, index=data_input.index, columns=target_ids)

        # Handle cases where a target location is exactly on a gauge
        if np.any(zero_dist_mask):
            target_indices, gauge_indices = np.where(zero_dist_mask)
            for t_idx, g_idx in zip(target_indices, gauge_indices):
                target_id = target_ids[t_idx]
                gauge_id = gauge_ids[g_idx]
                result_df[target_id] = data_input[gauge_id]

        return result_df


class KrigingInterpolator(BaseSpatialInterpolator):
    """
    Interpolates spatial data using Ordinary Kriging.
    This method is computationally intensive as it fits a model for each time step.
    """
    def __init__(self, variogram_model='linear', verbose=False, enable_plotting=False):
        self.variogram_model = variogram_model
        self.verbose = verbose
        self.enable_plotting = enable_plotting

    def interpolate(self, rain_gauges: List[RainGauge], target_locations: Dict[str, tuple]) -> pd.DataFrame:
        if not rain_gauges:
            raise ValueError("Rain gauges list cannot be empty.")

        gauge_ids = [g.id for g in rain_gauges]
        target_ids = list(target_locations.keys())
        gauge_coords = np.array([g.coords for g in rain_gauges])
        target_coords = np.array(list(target_locations.values()))

        gauge_x = gauge_coords[:, 0]
        gauge_y = gauge_coords[:, 1]
        target_x = target_coords[:, 0]
        target_y = target_coords[:, 1]

        data_input = self._combine_gauge_data(rain_gauges)

        interpolated_results = []
        for timestamp, series in data_input[gauge_ids].iterrows():
            rainfall_values = series.values

            # Skip Kriging if all values are NaN or the same, as it will fail
            if pd.isna(rainfall_values).all() or len(set(pd.Series(rainfall_values).dropna())) <= 1:
                 # Use the mean of non-nan values if they are all the same
                interpolated_step = np.full(len(target_ids), np.nanmean(rainfall_values))
            else:
                try:
                    # Filter out NaN values for Kriging calculation
                    valid_indices = ~pd.isna(rainfall_values)
                    if not np.any(valid_indices): # handle case where all are nan after filtering
                        interpolated_step = np.full(len(target_ids), np.nan)
                    else:
                        ok = OrdinaryKriging(
                            gauge_x[valid_indices], gauge_y[valid_indices], rainfall_values[valid_indices],
                            variogram_model=self.variogram_model,
                            verbose=self.verbose, enable_plotting=self.enable_plotting,
                        )
                        k_values, _ = ok.execute('points', target_x, target_y)
                        interpolated_step = k_values
                except Exception as e:
                    print(f"Warning: Kriging failed for timestamp {timestamp}. Falling back to mean. Error: {e}")
                    interpolated_step = np.full(len(target_ids), np.nanmean(rainfall_values))

            interpolated_results.append(interpolated_step)

        result_df = pd.DataFrame(
            interpolated_results,
            index=data_input.index,
            columns=target_ids
        )
        return result_df
