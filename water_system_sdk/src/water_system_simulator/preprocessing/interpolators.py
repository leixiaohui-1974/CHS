from abc import ABC, abstractmethod
from typing import List, Dict
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
from pykrige.ok import OrdinaryKriging
from water_system_simulator.preprocessing.structures import RainGauge


class BaseSpatialInterpolator(ABC):
    """
    Abstract base class for all spatial interpolation algorithms.
    """

    @abstractmethod
    def interpolate(
        self,
        rain_gauges: List[RainGauge],
        target_locations: Dict[str, tuple]
    ) -> pd.DataFrame:
        """
        Performs spatial interpolation of rainfall data.

        Args:
            rain_gauges (List[RainGauge]): A list of RainGauge objects, each
                                           containing its coordinates and rainfall
                                           time series data.
            target_locations (Dict[str, tuple]): A dictionary where keys are the
                                                 identifiers of the target locations
                                                 (e.g., sub-basin IDs) and values
                                                 are their (x, y) coordinates.

        Returns:
            pd.DataFrame: A DataFrame where the index is the timestamp and columns
                          are the target location identifiers. The values are the
                          interpolated rainfall for each location at each time step.
        """
        pass


class InverseDistanceWeightingInterpolator(BaseSpatialInterpolator):
    """
    Interpolates rainfall using the Inverse Distance Weighting (IDW) method.
    """
    def __init__(self, power: float = 2.0):
        """
        Initializes the IDW interpolator.

        Args:
            power (float): The power parameter (p) for weighting. Higher values
                           give more influence to closer points. Defaults to 2.0.
        """
        if power <= 0:
            raise ValueError("Power parameter must be greater than zero.")
        self.power = power

    def interpolate(
        self,
        rain_gauges: List[RainGauge],
        target_locations: Dict[str, tuple]
    ) -> pd.DataFrame:
        if not rain_gauges:
            raise ValueError("Rain gauges list cannot be empty.")

        # Combine all time series into a single DataFrame for easier access
        all_series = {g.id: g.time_series.iloc[:, 0] for g in rain_gauges}
        combined_df = pd.DataFrame(all_series)

        # Prepare arrays for calculation
        gauge_coords = np.array([g.coords for g in rain_gauges])
        target_coords = np.array(list(target_locations.values()))
        target_ids = list(target_locations.keys())

        # Calculate distances between each target and each gauge
        # Shape: (num_targets, num_gauges)
        distances = np.linalg.norm(target_coords[:, np.newaxis, :] - gauge_coords, axis=2)

        # Handle zero distance case: if a target is at a gauge, its value is the gauge's value
        zero_dist_mask = distances == 0

        # Calculate weights, avoiding division by zero
        with np.errstate(divide='ignore'):
            weights = 1.0 / (distances ** self.power)

        weights[np.isinf(weights)] = 0 # Clean up any infs that might have resulted from divide by zero

        # Sum of weights for each target location
        sum_of_weights = np.sum(weights, axis=1, keepdims=True)

        # Normalize weights
        # If sum_of_weights is zero for a target, it means all distances were zero or inf.
        # This case is handled by the zero_dist_mask, so we can safely divide.
        normalized_weights = np.divide(weights, sum_of_weights, where=sum_of_weights!=0)

        # Get rainfall values from gauges for all timesteps
        # Shape: (num_timesteps, num_gauges)
        rainfall_values = combined_df.values

        # Perform the weighted average for all timesteps at once using matrix multiplication
        # Result shape: (num_timesteps, num_targets)
        interpolated_values = np.dot(rainfall_values, normalized_weights.T)

        # Create the result DataFrame
        result_df = pd.DataFrame(interpolated_values, index=combined_df.index, columns=target_ids)

        # Now, handle the cases where a target location is exactly on a gauge
        if np.any(zero_dist_mask):
            target_indices, gauge_indices = np.where(zero_dist_mask)
            for t_idx, g_idx in zip(target_indices, gauge_indices):
                target_id = target_ids[t_idx]
                gauge_id = rain_gauges[g_idx].id
                result_df[target_id] = combined_df[gauge_id]

        return result_df


class KrigingInterpolator(BaseSpatialInterpolator):
    """
    Interpolates rainfall using Ordinary Kriging.

    This method is more advanced and accounts for spatial autocorrelation.
    It fits a model for each time step, which can be computationally expensive.
    """
    def __init__(self, variogram_model='linear', verbose=False, enable_plotting=False):
        """
        Initializes the Kriging interpolator.

        Args:
            variogram_model (str): The variogram model to use. Common options
                                   are 'linear', 'power', 'gaussian', 'spherical'.
            verbose (bool): If True, prints status messages from the Kriging solver.
            enable_plotting (bool): If True, allows pykrige to generate plots
                                    (can be resource-intensive).
        """
        self.variogram_model = variogram_model
        self.verbose = verbose
        self.enable_plotting = enable_plotting

    def interpolate(
        self,
        rain_gauges: List[RainGauge],
        target_locations: Dict[str, tuple]
    ) -> pd.DataFrame:
        if not rain_gauges:
            raise ValueError("Rain gauges list cannot be empty.")

        all_series = {g.id: g.time_series.iloc[:, 0] for g in rain_gauges}
        combined_df = pd.DataFrame(all_series)

        gauge_coords = np.array([g.coords for g in rain_gauges])
        target_coords = np.array(list(target_locations.values()))
        target_ids = list(target_locations.keys())

        gauge_x = gauge_coords[:, 0]
        gauge_y = gauge_coords[:, 1]
        target_x = target_coords[:, 0]
        target_y = target_coords[:, 1]

        interpolated_results = []

        # Iterate over each time step
        for timestamp, series in combined_df.iterrows():
            rainfall_values = series.values

            # Skip interpolation if all gauge values are NaN or the same
            if np.all(np.isnan(rainfall_values)) or np.all(rainfall_values == rainfall_values[0]):
                # If all same, just use that value for all targets
                interpolated_step = np.full(len(target_ids), rainfall_values[0])
            else:
                try:
                    # Create and execute the Ordinary Kriging model
                    ok = OrdinaryKriging(
                        gauge_x,
                        gauge_y,
                        rainfall_values,
                        variogram_model=self.variogram_model,
                        verbose=self.verbose,
                        enable_plotting=self.enable_plotting,
                    )
                    # k_values are the interpolated values, ss_values are the variances
                    k_values, ss_values = ok.execute('points', target_x, target_y)
                    interpolated_step = k_values
                except Exception as e:
                    # If Kriging fails for a step, fall back to a simpler method like IDW
                    # For now, we'll just fill with the mean of the gauges for this step
                    print(f"Warning: Kriging failed for timestamp {timestamp} with error: {e}. Falling back to mean.")
                    interpolated_step = np.full(len(target_ids), np.nanmean(rainfall_values))

            interpolated_results.append(interpolated_step)

        # Create the final DataFrame
        result_df = pd.DataFrame(
            interpolated_results,
            index=combined_df.index,
            columns=target_ids
        )

        return result_df


class ThiessenPolygonInterpolator(BaseSpatialInterpolator):
    """
    Interpolates rainfall using the Thiessen Polygon (or Nearest Neighbor) method.
    Each target location is assigned the rainfall value of the nearest rain gauge.
    """
    def interpolate(
        self,
        rain_gauges: List[RainGauge],
        target_locations: Dict[str, tuple]
    ) -> pd.DataFrame:
        if not rain_gauges:
            raise ValueError("Rain gauges list cannot be empty.")

        # Combine all time series into a single DataFrame for easier access
        all_series = {g.id: g.time_series.iloc[:, 0] for g in rain_gauges}
        combined_df = pd.DataFrame(all_series)

        # Prepare arrays for nearest neighbor search
        gauge_coords = np.array([g.coords for g in rain_gauges])
        gauge_ids = [g.id for g in rain_gauges]
        target_coords = np.array(list(target_locations.values()))
        target_ids = list(target_locations.keys())

        # Use cKDTree for efficient nearest neighbor lookup
        kdtree = cKDTree(gauge_coords)
        distances, indices = kdtree.query(target_coords, k=1)

        # Create the result DataFrame
        result_df = pd.DataFrame(index=combined_df.index, columns=target_ids)

        # Assign the time series of the nearest gauge to each target location
        for i, target_id in enumerate(target_ids):
            nearest_gauge_index = indices[i]
            nearest_gauge_id = gauge_ids[nearest_gauge_index]
            result_df[target_id] = combined_df[nearest_gauge_id]

        return result_df
