from typing import List
from water_system_simulator.modeling.base_model import BaseModel
from water_system_simulator.modeling.hydrology.sub_basin import SubBasin
from .strategies import BaseRunoffModel, BaseRoutingModel


class SemiDistributedHydrologyModel(BaseModel):
    """
    A semi-distributed hydrological model that uses strategy pattern to simulate
    runoff and routing for a watershed composed of multiple sub-basins.
    """

    def __init__(
        self,
        sub_basins: List[SubBasin],
        runoff_strategy: BaseRunoffModel,
        routing_strategy: BaseRoutingModel,
        **kwargs
    ):
        """
        Initializes the SemiDistributedHydrologyModel.

        Args:
            sub_basins (List[SubBasin]): A list of SubBasin objects that make up the watershed.
            runoff_strategy (BaseRunoffModel): The strategy for calculating runoff.
            routing_strategy (BaseRoutingModel): The strategy for routing flow.
            **kwargs: Additional keyword arguments for the BaseModel.
        """
        super().__init__(**kwargs)
        self.sub_basins = sub_basins
        self.runoff_strategy = runoff_strategy
        self.routing_strategy = routing_strategy
        self.output = 0.0  # Initialize output

    def step(self, dt: float, t: float, **kwargs):
        """
        Executes a single time step for the entire watershed model.

        It calculates the outflow from each sub-basin using the provided strategies
        and sums them up to get the total watershed outflow.

        Args:
            dt (float): The time step in hours.
            t (float): The current simulation time.
            **kwargs: Must contain 'precipitation' (in mm/hr) for the current time step.
        """
        precipitation_per_hour = kwargs.get('precipitation', 0.0)
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
        return {
            "output": self.output,
            "runoff_strategy_state": self.runoff_strategy.get_state(),
            "routing_strategy_state": self.routing_strategy.get_state(),
        }
