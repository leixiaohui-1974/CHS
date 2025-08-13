from typing import List, Optional, Dict, Any
from water_system_simulator.modeling.base_model import BaseModel
from water_system_simulator.modeling.hydrology.sub_basin import SubBasin
from .strategies import BaseRunoffModel, BaseRoutingModel
from water_system_simulator.data_processing.processors import (
    BaseDataProcessor, DataCleaner, InverseDistanceWeightingInterpolator,
    ThiessenPolygonInterpolator, KrigingInterpolator, UnitConverter, TimeResampler
)

# A factory to map processor types from config to their classes
PROCESSOR_FACTORY: Dict[str, Any] = {
    "DataCleaner": DataCleaner,
    "InverseDistanceWeightingInterpolator": InverseDistanceWeightingInterpolator,
    "ThiessenPolygonInterpolator": ThiessenPolygonInterpolator,
    "KrigingInterpolator": KrigingInterpolator,
    "UnitConverter": UnitConverter,
    "TimeResampler": TimeResampler,
}


class SemiDistributedHydrologyModel(BaseModel):
    """
    A semi-distributed hydrological model that uses strategy pattern to simulate
    runoff and routing for a watershed composed of multiple sub-basins.
    It now includes an internal data processing pipeline.
    """

    def __init__(
        self,
        sub_basins: List[SubBasin],
        runoff_strategy: BaseRunoffModel,
        routing_strategy: BaseRoutingModel,
        data_pipeline: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        """
        Initializes the SemiDistributedHydrologyModel.

        Args:
            sub_basins (List[SubBasin]): A list of SubBasin objects that make up the watershed.
            runoff_strategy (BaseRunoffModel): The strategy for calculating runoff.
            routing_strategy (BaseRoutingModel): The strategy for routing flow.
            data_pipeline (Optional[List[Dict]]): Configuration for the data processing pipeline.
            **kwargs: Additional keyword arguments for the BaseModel.
        """
        super().__init__(**kwargs)
        self.sub_basins = sub_basins
        self.runoff_strategy = runoff_strategy
        self.routing_strategy = routing_strategy
        self.output = 0.0  # Initialize output

        self.data_pipeline: List[BaseDataProcessor] = []
        if data_pipeline:
            for step_config in data_pipeline:
                step_type = step_config.get("type")
                step_params = step_config.get("params", {})
                if step_type in PROCESSOR_FACTORY:
                    processor_class = PROCESSOR_FACTORY[step_type]
                    # Pass id from config if available, otherwise use step_type
                    step_params['id'] = step_params.get('id', step_type)
                    self.data_pipeline.append(processor_class(**step_params))
                else:
                    raise ValueError(f"Unknown data processor type: {step_type}")

    def _execute_pipeline(self, raw_data: Any) -> Any:
        """Processes raw data through the configured pipeline."""
        processed_data = raw_data
        for processor in self.data_pipeline:
            processed_data = processor.process(processed_data)
        return processed_data

    def step(self, dt: float, t: float, **kwargs):
        """
        Executes a single time step for the entire watershed model.

        It first processes raw input data through its pipeline, then calculates
        outflow from each sub-basin and sums them up to get the total watershed outflow.

        Args:
            dt (float): The time step in hours.
            t (float): The current simulation time.
            **kwargs: Must contain 'raw_rainfall' for the current time step.
        """
        raw_rainfall = kwargs.get('raw_rainfall', 0.0)

        # Execute the data processing pipeline
        precipitation_per_hour = self._execute_pipeline(raw_rainfall)

        # Convert precipitation from mm/hr to mm for the time step
        precipitation_mm = precipitation_per_hour * dt

        total_outflow_m3_per_s = 0.0
        for sub_basin in self.sub_basins:
            # 1. Call the runoff strategy to calculate effective rainfall
            effective_rainfall_mm = self.runoff_strategy.calculate_runoff(
                rainfall=precipitation_mm,
                sub_basin_params=sub_basin.params,
                dt=dt
            )

            # 2. Call the routing strategy to calculate outflow
            sub_basin_outflow = self.routing_strategy.route_flow(
                effective_rainfall=effective_rainfall_mm,
                sub_basin_params=sub_basin.params,
                dt=dt
            )
            total_outflow_m3_per_s += sub_basin_outflow

        self.output = total_outflow_m3_per_s
        return self.output

    def get_state(self):
        """
        Returns the aggregated state of the model, including strategy states.
        """
        pipeline_state = {p.id: p.get_state() for p in self.data_pipeline}
        return {
            "output": self.output,
            "runoff_strategy_state": self.runoff_strategy.get_state(),
            "routing_strategy_state": self.routing_strategy.get_state(),
            "data_pipeline_state": pipeline_state,
        }
