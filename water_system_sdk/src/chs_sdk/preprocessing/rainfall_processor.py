import pandas as pd
from typing import Dict, Any
from chs_sdk.modeling.base_model import BaseModel
from chs_sdk.preprocessing.interpolators import BaseSpatialInterpolator
from chs_sdk.preprocessing.structures import RainGauge


class RainfallProcessor(BaseModel):
    """
    A preprocessing component that generates spatially distributed rainfall
    for hydrological models using a specified interpolation strategy.
    """

    def __init__(self, strategy: BaseSpatialInterpolator, source_dataset: str, **kwargs):
        """
        Initializes the RainfallProcessor.

        Args:
            strategy (BaseSpatialInterpolator): The interpolation algorithm to use.
            source_dataset (str): The key of the rain gauge dataset in the main
                                  simulation config's 'datasets' section.
            **kwargs: Additional keyword arguments for the BaseModel.
        """
        super().__init__(**kwargs)
        self.strategy = strategy
        self.source_dataset = source_dataset
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
        # 1. Load rain gauge data from the config
        try:
            gauge_configs = sim_manager.config['datasets'][self.source_dataset]
        except KeyError:
            raise ValueError(f"Dataset '{self.source_dataset}' not found in config's 'datasets' section.")

        rain_gauges = []
        for gauge_info in gauge_configs:
            try:
                # Assuming time_series_path is relative to the execution directory
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
                raise FileNotFoundError(f"Rainfall data file not found at: {gauge_info['time_series_path']}")
            except Exception as e:
                raise IOError(f"Error reading data for gauge {gauge_info['id']}: {e}")

        # 2. Collect target locations from all hydrological models in the simulation
        target_locations = {}
        # This requires a way to identify hydrological models. For now, we assume
        # they have a 'sub_basins' attribute. This might need refinement.
        for name, component in sim_manager.components.items():
            if hasattr(component, 'sub_basins'):
                for sub_basin in component.sub_basins:
                    # Assuming sub_basin has 'id' and 'coords' attributes
                    target_locations[sub_basin.id] = sub_basin.coords

        if not target_locations:
            raise ValueError("No target locations (sub-basins with coordinates) found in any component.")

        # 3. Call the interpolation strategy
        self.interpolated_rainfall = self.strategy.interpolate(
            rain_gauges=rain_gauges,
            target_locations=target_locations
        )

    def get_state(self):
        """
        Exposes the component's state. The interpolated_rainfall is the primary output.
        """
        state = super().get_state()
        state['interpolated_rainfall'] = self.interpolated_rainfall
        return state
