import logging
import pandas as pd
from typing import Dict, TYPE_CHECKING
from chs_sdk.modules.modeling.base_model import BaseModel
from chs_sdk.preprocessing.interpolators import BaseSpatialInterpolator
from chs_sdk.preprocessing.structures import RainGauge

if TYPE_CHECKING:
    from chs_sdk.simulation_manager import SimulationManager


class RainfallProcessor:
    """
    A preprocessing component that generates spatially distributed rainfall
    for hydrological models using a specified interpolation strategy.

    This component runs before the main simulation loop to prepare all necessary
    rainfall data.
    """

    def __init__(self, strategy: BaseSpatialInterpolator, source_dataset: str, id: str, **kwargs):
        """
        Initializes the RainfallProcessor.

        Args:
            strategy (BaseSpatialInterpolator): An instance of an interpolation
                                                algorithm to use (e.g., KrigingInterpolator).
            source_dataset (str): The key of the rain gauge dataset in the main
                                  simulation config's 'datasets' section.
            id (str): The unique identifier for this component.
            **kwargs: Additional keyword arguments.
        """
        if not isinstance(strategy, BaseSpatialInterpolator):
            raise TypeError("The 'strategy' must be an instance of a class that inherits from BaseSpatialInterpolator.")
        self.strategy = strategy
        self.source_dataset = source_dataset
        self.id = id
        self.interpolated_rainfall: pd.DataFrame = None

    def run_preprocessing(self, sim_manager: 'SimulationManager'):
        """
        Executes the rainfall interpolation. This method is called by the
        SimulationManager before the main simulation loop starts.

        Args:
            sim_manager (SimulationManager): The simulation manager instance,
                                             providing access to the config and
                                             other components.
        """
        logging.info(f"[{self.id}] Running rainfall preprocessing...")
        # 1. Load rain gauge data from the config
        try:
            # Access datasets via attribute on the Pydantic config model
            gauge_configs = sim_manager.config.datasets[self.source_dataset]
            logging.info(f"[{self.id}] Found {len(gauge_configs)} rain gauges in dataset '{self.source_dataset}'.")
        except KeyError:
            logging.error(f"Dataset '{self.source_dataset}' not found in config's 'datasets' section.")
            raise ValueError(f"Dataset '{self.source_dataset}' not found in config's 'datasets' section.")

        rain_gauges = []
        for gauge_info in gauge_configs:
            try:
                ts_df = pd.read_csv(
                    gauge_info['time_series_path'],
                    index_col=0,
                    parse_dates=True
                )
                rain_gauges.append(
                    RainGauge(
                        id=gauge_info['id'],
                        coords=tuple(gauge_info['coords']),
                        time_series=ts_df
                    )
                )
            except FileNotFoundError:
                logging.error(f"Rainfall data file not found at: {gauge_info['time_series_path']}")
                raise
            except Exception as e:
                logging.error(f"Error reading data for gauge {gauge_info['id']}: {e}")
                raise IOError(f"Error reading data for gauge {gauge_info['id']}") from e

        # 2. Collect target locations (sub-basin centroids) from all hydrological models
        target_locations = {}
        # This assumes hydrological models have a 'sub_basins' attribute.
        for component in sim_manager.components.values():
            if hasattr(component, 'sub_basins') and isinstance(getattr(component, 'sub_basins'), list):
                for sub_basin in component.sub_basins:
                    if hasattr(sub_basin, 'id') and hasattr(sub_basin, 'coords'):
                        target_locations[sub_basin.id] = sub_basin.coords
                    else:
                        logging.warning(f"Component '{component.id}' has a sub-basin object without 'id' or 'coords'.")

        if not target_locations:
            logging.error("No target locations (sub-basins with centroids) found in any component.")
            raise ValueError("No target locations (sub-basins with centroids) found in any component.")
        logging.info(f"[{self.id}] Found {len(target_locations)} target locations for interpolation.")

        # 3. Call the interpolation strategy
        logging.info(f"[{self.id}] Applying '{self.strategy.__class__.__name__}' interpolation strategy.")
        self.interpolated_rainfall = self.strategy.interpolate(
            rain_gauges=rain_gauges,
            target_locations=target_locations
        )
        logging.info(f"[{self.id}] Rainfall interpolation complete. Result shape: {self.interpolated_rainfall.shape}")

    def get_state(self) -> Dict:
        """
        Exposes the component's state. The interpolated_rainfall is the primary output.
        """
        state = {"interpolated_rainfall": self.interpolated_rainfall}
        return state
