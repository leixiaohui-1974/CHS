from typing import List

from water_system_sdk.src.water_system_simulator.modeling.base_model import BaseModel
from water_system_sdk.src.water_system_simulator.modeling.hydrology.sub_basin import SubBasin

class SemiDistributedHydrologyModel(BaseModel):
    """
    A semi-distributed hydrological model that simulates runoff and routing
    for a watershed composed of multiple sub-basins.
    """
    def __init__(self, sub_basins: List[SubBasin], **kwargs):
        """
        Initializes the SemiDistributedHydrologyModel.

        Args:
            sub_basins (List[SubBasin]): A list of SubBasin objects that make up the watershed.
            **kwargs: Additional keyword arguments for the BaseModel.
        """
        super().__init__(**kwargs)
        self.sub_basins = sub_basins
        self.output = 0.0  # Initialize output

    def step(self, dt: float, t: float, **kwargs):
        """
        Executes a single time step for the entire watershed model.

        It calculates the outflow from each sub-basin and sums them up to get the
        total watershed outflow.

        Args:
            dt (float): The time step in hours.
            t (float): The current simulation time.
            **kwargs: Must contain 'precipitation' (in mm/hr) and 'evaporation' (in mm/hr)
                      values for the current time step.
        """
        precipitation = kwargs.get('precipitation', 0.0)
        evaporation = kwargs.get('evaporation', 0.0)

        total_outflow_m3_per_s = 0.0
        for sub_basin in self.sub_basins:
            sub_basin_outflow = sub_basin.step(precipitation, evaporation, dt)
            total_outflow_m3_per_s += sub_basin_outflow

        self.output = total_outflow_m3_per_s
        return self.output

    def get_state(self):
        """
        Returns the aggregated state of all sub-basins.
        """
        sub_basin_states = {f"sub_basin_{i}": sb.get_state() for i, sb in enumerate(self.sub_basins)}
        return {
            "output": self.output,
            "sub_basins": sub_basin_states
        }
