import pandas as pd
from typing import List, Union
from chs_sdk.modules.modeling.base_model import BaseModel
from chs_sdk.modules.modeling.hydrology.sub_basin import SubBasin
from .strategies import BaseRunoffModel, BaseRoutingModel


import numpy as np

class SemiDistributedHydrologyModel(BaseModel):
    """
    A semi-distributed hydrological model that uses strategy pattern to simulate
    runoff and routing for a watershed composed of multiple sub-basins.
    This version is optimized for vectorization.
    """

    def __init__(
        self,
        sub_basins: List[dict],
        runoff_strategy: BaseRunoffModel,
        routing_strategy: BaseRoutingModel,
        **kwargs
    ):
        """
        Initializes the SemiDistributedHydrologyModel.
        """
        super().__init__(**kwargs)
        self.runoff_strategy = runoff_strategy
        self.routing_strategy = routing_strategy
        self.output = 0.0
        self.input_rainfall: Union[pd.DataFrame, None] = None

        # Create and store SubBasin objects so other components can inspect them
        self.sub_basins = [SubBasin(**sb_data) for sb_data in sub_basins]

        # --- Vectorization Setup ---
        num_basins = len(sub_basins)
        self.num_basins = num_basins

        # Create structured array for parameters for better organization
        param_dtype = [
            ('area', 'f4'), ('WM', 'f4'), ('B', 'f4'), ('IM', 'f4'), # Runoff
            ('K', 'f4'), ('x', 'f4') # Routing
        ]
        self.params = np.zeros(num_basins, dtype=param_dtype)

        # Initialize parameter and state arrays
        self.runoff_state_W = np.zeros(num_basins, dtype=np.float32)
        self.routing_state_I_prev = np.zeros(num_basins, dtype=np.float32)
        self.routing_state_O_prev = np.zeros(num_basins, dtype=np.float32)

        for i, sb_info in enumerate(sub_basins):
            p = sb_info['params']
            self.params[i] = (
                sb_info['area'], p.get('WM', 100), p.get('B', 0.3), p.get('IM', 0.05),
                p.get('K', 12), p.get('x', 0.2)
            )
            # Initialize states from config
            self.runoff_state_W[i] = p.get('initial_W', self.params[i]['WM'] * 0.5)
            self.routing_state_I_prev[i] = p.get('initial_inflow', 0.0)
            self.routing_state_O_prev[i] = p.get('initial_outflow', 0.0)


    def step(self, dt: float, t: float, **kwargs):
        """
        Executes a single time step for the entire watershed model using vectorized operations.
        """
        precip_vector = np.zeros(self.num_basins, dtype=np.float32)
        if self.input_rainfall is not None and not self.input_rainfall.empty:
            # Find the row corresponding to the current time t
            # We use a tolerance to handle potential floating point inaccuracies
            time_slice = self.input_rainfall[np.isclose(self.input_rainfall.index.values, t)]
            if not time_slice.empty:
                # Get the rainfall for each sub-basin by its ID
                sub_basin_ids = [sb.id for sb in self.sub_basins]
                # Ensure all sub-basin IDs are present in the dataframe columns
                if all(sid in time_slice.columns for sid in sub_basin_ids):
                    precip_values = time_slice[sub_basin_ids].iloc[0].values
                    # The input is assumed to be in mm/hr, convert to mm for the time step
                    precip_vector = precip_values * dt
                else:
                    # Fallback or error if a sub-basin's data is missing
                    pass # Defaulting to zeros
        else:
            # Fallback to uniform precipitation if no spatial data is provided
            uniform_precip_per_hour = kwargs.get('precipitation', 0.0)
            uniform_precip_mm = uniform_precip_per_hour * dt
            precip_vector = np.full(self.num_basins, uniform_precip_mm, dtype=np.float32)


        # 1. Call the (vectorized) runoff strategy
        effective_rainfall_mm, self.runoff_state_W = self.runoff_strategy.calculate_runoff_vectorized(
            rainfall_vector=precip_vector,
            W_initial=self.runoff_state_W,
            params=self.params,
            dt=dt
        )

        # 2. Call the (vectorized) routing strategy
        outflow_vector, self.routing_state_I_prev, self.routing_state_O_prev = self.routing_strategy.route_flow_vectorized(
            effective_rainfall_vector=effective_rainfall_mm,
            I_prev=self.routing_state_I_prev,
            O_prev=self.routing_state_O_prev,
            params=self.params,
            dt=dt
        )

        # 3. Sum the outflows from all sub-basins
        total_outflow_m3_per_s = np.sum(outflow_vector)

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
