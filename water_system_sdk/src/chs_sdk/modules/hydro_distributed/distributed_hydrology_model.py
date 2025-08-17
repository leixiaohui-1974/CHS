import numpy as np
from collections import deque
from typing import Optional, Dict, Any, Tuple
from .gistools import GISTools
from .hydrological_unit import HydrologicalUnit
from .routing import identify_river_network, HillslopeRouting, ChannelRouting
from chs_sdk.modeling.base_model import BaseModel

class DistributedHydrologyModel(BaseModel):
    """
    A fully distributed, grid-based hydrological model.
    """
    def __init__(self, dem: np.ndarray, curve_number_grid: np.ndarray, cell_size: float = 30.0,
                 channel_threshold: int = 100, routing_params: Optional[Dict[str, float]] = None) -> None:
        """
        Initializes the distributed hydrological model.

        Args:
            dem (np.ndarray): The Digital Elevation Model grid.
            curve_number_grid (np.ndarray): A grid of SCS Curve Numbers for each cell.
            cell_size (float): The grid cell size in meters.
            channel_threshold (int): Flow accumulation threshold to define channels.
            routing_params (dict): Parameters for channel routing, e.g., {'k': 3.0, 'x': 0.2}.
        """
        super().__init__()

        # --- 1. GIS Preprocessing ---
        self.dem: np.ndarray = GISTools.fill_sinks(dem)
        self.fdr: np.ndarray = GISTools.flow_direction(self.dem)
        self.fac: np.ndarray = GISTools.flow_accumulation(self.fdr)

        # --- 2. Initialize Hydrological Units (Cells) ---
        rows, cols = dem.shape
        self.hydro_units: np.ndarray = np.empty((rows, cols), dtype=object)
        for r in range(rows):
            for c in range(cols):
                if dem[r,c] > 0: # Assuming negative values are no-data
                    self.hydro_units[r,c] = HydrologicalUnit(curve_number=int(curve_number_grid[r,c]))

        # --- 3. Initialize Routing Components ---
        self.channel_network: np.ndarray = identify_river_network(self.fac, channel_threshold)

        self.hillslope_router: HillslopeRouting = HillslopeRouting(self.dem, self.fdr, cell_size)
        self.travel_times: np.ndarray = self.hillslope_router.calculate_travel_times(self.channel_network)
        # Convert travel times from seconds to integer timesteps (assuming dt=1hr)
        # Handle inf values properly before casting
        valid_times: np.ndarray = self.travel_times[np.isfinite(self.travel_times)]
        self.travel_times_steps: np.ndarray = np.full_like(self.travel_times, -1, dtype=int)
        self.travel_times_steps[np.isfinite(self.travel_times)] = (valid_times / 3600.0).astype(int)

        default_routing_params: Dict[str, float] = {'k': 3.0, 'x': 0.2, 'dt': 1.0}
        if routing_params:
            default_routing_params.update(routing_params)

        self.channel_router: ChannelRouting = ChannelRouting(
            self.fdr, self.channel_network,
            k=default_routing_params['k'],
            x=default_routing_params['x'],
            dt=default_routing_params['dt']
        )

        # --- 4. State Variables ---
        r_idx, c_idx = np.unravel_index(np.argmax(self.fac), self.fac.shape)
        self.outlet_r: int = int(r_idx)
        self.outlet_c: int = int(c_idx)
        self.surface_runoff_grid: np.ndarray = np.zeros_like(self.dem, dtype=float)

        # Initialize runoff history buffer
        valid_travel_times = self.travel_times_steps[self.travel_times_steps >= 0]
        max_travel_time: int
        if valid_travel_times.size > 0:
            max_travel_time = int(np.max(valid_travel_times))
        else:
            max_travel_time = 0
        self.runoff_history: deque = deque(maxlen=int(max_travel_time) + 1)

        # Pre-calculate D8 offsets for faster lookups
        self.d8_to_offset = {
            1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1),
            16: (0, -1), 32: (-1, -1), 64: (-1, 0), 128: (-1, 1)
        }

    def _find_channel_destination(self, r_start: int, c_start: int) -> Tuple[Optional[int], Optional[int]]:
        """Traces a flow path from a starting cell to the first channel cell."""
        r, c = r_start, c_start
        for _ in range(self.dem.size): # Max path length is the total number of cells
            if self.channel_network[r, c]:
                return r, c

            direction = int(self.fdr[r,c])
            if direction in self.d8_to_offset:
                dr, dc = self.d8_to_offset[direction]
                r, c = r + dr, c + dc

                if not (0 <= r < self.dem.shape[0] and 0 <= c < self.dem.shape[1]):
                    return None, None # Flowed off the map
            else:
                return None, None # Reached a sink or flat area not in channel
        return None, None # Path is too long (cycle)

    def step(self, rainfall_grid: np.ndarray, et_grid: Optional[np.ndarray] = None, **kwargs: Any) -> None:
        """
        Represents a single time step of the model's execution.

        Args:
            rainfall_grid: A 2D grid of rainfall (mm) for the current time step.
            et_grid: A 2D grid of potential ET (mm) for the current time step.
        """
        if et_grid is None:
            et_grid = np.zeros_like(rainfall_grid)

        # --- 1. Calculate surface runoff from vertical processes ---
        self.surface_runoff_grid.fill(0)
        rows, cols = self.dem.shape
        for r in range(rows):
            for c in range(cols):
                hydro_unit = self.hydro_units[r, c]
                if hydro_unit is not None:
                    runoff = hydro_unit.update_state(
                        rainfall_mm=float(rainfall_grid[r, c]),
                        pot_et_mm=float(et_grid[r, c])
                    )
                    self.surface_runoff_grid[r, c] = runoff

        # --- 2. Hillslope Routing (Time-Area Method with Runoff History) ---
        self.runoff_history.append(self.surface_runoff_grid)

        # Calculate lateral inflows arriving at the channel in this timestep
        lateral_inflows: np.ndarray = np.zeros_like(self.dem, dtype=float)

        # Iterate over each cell to see if its past runoff arrives now
        for r in range(rows):
            for c in range(cols):
                # If it's a hillslope cell with valid travel time
                if not self.channel_network[r,c] and self.travel_times_steps[r,c] > 0:
                    travel_time = int(self.travel_times_steps[r,c])

                    # Check if we have enough history
                    if travel_time < len(self.runoff_history):
                        # Get the runoff that was generated 'travel_time' steps ago
                        past_runoff = self.runoff_history[-travel_time - 1][r, c]

                        # Find the destination channel cell and add the inflow
                        dest_r, dest_c = self._find_channel_destination(r, c)
                        if dest_r is not None and dest_c is not None:
                            lateral_inflows[dest_r, dest_c] += past_runoff

        # --- 3. Channel Routing ---
        channel_outflows: np.ndarray = self.channel_router.route_flows(lateral_inflows)

        # The main output required by the SDK's BaseModel
        self.output = channel_outflows[self.outlet_r, self.outlet_c]

    def get_state(self) -> Dict[str, Any]:
        """
        Returns a dictionary of the model's current state.
        """
        rows, cols = self.dem.shape
        soil_moisture_grid: np.ndarray = np.zeros((rows, cols), dtype=float)
        for r in range(rows):
            for c in range(cols):
                hydro_unit = self.hydro_units[r, c]
                if hydro_unit is not None:
                    soil_moisture_grid[r, c] = hydro_unit.soil_moisture

        return {
            "soil_moisture": soil_moisture_grid,
            "channel_outflow": self.channel_router.prev_outflow,
            "outlet_discharge": self.output
        }
