import numpy as np
from collections import deque

def identify_river_network(fac: np.ndarray, threshold: int):
    """
    Identifies the river network from a flow accumulation grid.

    Args:
        fac (np.ndarray): The flow accumulation grid.
        threshold (int): The number of upstream cells required to initiate a channel.

    Returns:
        np.ndarray: A boolean grid where True represents a channel cell.
    """
    return fac > threshold

class HillslopeRouting:
    """
    Handles routing of runoff from hillslope cells to the nearest channel
    by calculating travel times.
    """
    def __init__(self, dem: np.ndarray, fdr: np.ndarray, cell_size: float = 30.0):
        """
        Initializes the hillslope routing model.

        Args:
            dem (np.ndarray): The elevation grid (m).
            fdr (np.ndarray): The flow direction grid (D8).
            cell_size (float): The size of a grid cell in meters.
        """
        self.dem = dem
        self.fdr = fdr
        self.cell_size = cell_size
        self.travel_time_grid = np.zeros_like(dem, dtype=float)

        # Map D8 codes to (dr, dc, distance_multiplier)
        self.d8_info = {
            1: (0, 1, 1), 2: (1, 1, 1.414), 4: (1, 0, 1), 8: (1, -1, 1.414),
            16: (0, -1, 1), 32: (-1, -1, 1.414), 64: (-1, 0, 1), 128: (-1, 1, 1.414)
        }

    def calculate_travel_times(self, channel_network: np.ndarray, velocity_coefficient: float = 0.5):
        """
        Calculates the travel time from each hillslope cell to the nearest channel.
        This is done by traversing upstream from the channel cells.

        Args:
            channel_network (np.ndarray): Boolean grid where True is a channel.
            velocity_coefficient (float): A coefficient for the velocity calculation (v = C * sqrt(slope)).
        """
        rows, cols = self.dem.shape
        self.travel_time_grid = np.full_like(self.dem, -1.0, dtype=float)

        # Queue for upstream traversal, starting from channel cells
        queue = deque()
        for r in range(rows):
            for c in range(cols):
                if channel_network[r, c]:
                    self.travel_time_grid[r, c] = 0.0
                    queue.append((r, c))

        # Find all cells that flow INTO a given cell (pre-calculate upstream neighbors)
        upstream_neighbors = [[[] for _ in range(cols)] for _ in range(rows)]
        for r in range(rows):
            for c in range(cols):
                direction = self.fdr[r, c]
                if direction in self.d8_info:
                    dr, dc, _ = self.d8_info[direction]
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        upstream_neighbors[nr][nc].append((r, c))

        # Traverse upstream from the channel network
        while queue:
            r, c = queue.popleft()

            for ur, uc in upstream_neighbors[r][c]:
                if self.travel_time_grid[ur, uc] == -1.0: # If not yet processed

                    # Calculate velocity and time for the upstream cell (uc, ur) to flow to (c,r)
                    slope = (self.dem[ur, uc] - self.dem[r, c]) / (self.d8_info[self.fdr[ur, uc]][2] * self.cell_size)
                    slope = max(slope, 0.001) # Avoid zero or negative slope
                    velocity = velocity_coefficient * np.sqrt(slope)

                    flow_length = self.d8_info[self.fdr[ur, uc]][2] * self.cell_size
                    time_to_cross_cell = flow_length / velocity if velocity > 0 else np.inf

                    self.travel_time_grid[ur, uc] = self.travel_time_grid[r, c] + time_to_cross_cell
                    queue.append((ur, uc))

        # Set any remaining unprocessed cells (e.g. sinks) to a high travel time
        self.travel_time_grid[self.travel_time_grid == -1.0] = np.inf
        return self.travel_time_grid

class ChannelRouting:
    """
    Handles routing of water through the channel network using the Muskingum method.
    """
    def __init__(self, fdr: np.ndarray, channel_network: np.ndarray, k: float, x: float, dt: float):
        """
        Initializes the channel routing model.

        Args:
            fdr (np.ndarray): The flow direction grid.
            channel_network (np.ndarray): The boolean channel network grid.
            k (float): Muskingum storage time constant (units should match dt).
            x (float): Muskingum weighting factor (0 to 0.5).
            dt (float): Time step duration.
        """
        self.fdr = fdr
        self.channel_network = channel_network
        self.k = k
        self.x = x
        self.dt = dt

        # Pre-calculate Muskingum coefficients
        denominator = self.k * (1 - self.x) + 0.5 * self.dt
        if denominator == 0:
            raise ValueError("Muskingum denominator is zero. Check K, x, and dt.")
        self.c1 = (0.5 * self.dt - self.k * self.x) / denominator
        self.c2 = (0.5 * self.dt + self.k * self.x) / denominator
        self.c3 = (self.k * (1 - self.x) - 0.5 * self.dt) / denominator

        # State variables: Inflow and Outflow for each channel cell from the previous step
        self.prev_inflow = np.zeros_like(fdr, dtype=float)
        self.prev_outflow = np.zeros_like(fdr, dtype=float)

        # Get channel cells in upstream-to-downstream order
        self.channel_cells_ordered = self._topological_sort(fdr, channel_network)

        self.d8_to_offset = {
            1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1),
            16: (0, -1), 32: (-1, -1), 64: (-1, 0), 128: (-1, 1)
        }

    def _topological_sort(self, fdr, channel_network):
        """Topologically sorts the channel network for routing."""
        rows, cols = fdr.shape
        in_degree = np.zeros_like(fdr, dtype=int)

        channel_indices = np.argwhere(channel_network)

        for r, c in channel_indices:
            direction = fdr[r, c]
            if direction in self.d8_to_offset:
                dr, dc = self.d8_to_offset[direction]
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and channel_network[nr, nc]:
                    in_degree[nr, nc] += 1

        queue = deque([(r, c) for r, c in channel_indices if in_degree[r, c] == 0])
        ordered_list = []
        while queue:
            r, c = queue.popleft()
            ordered_list.append((r, c))

            direction = fdr[r, c]
            if direction in self.d8_to_offset:
                dr, dc = self.d8_to_offset[direction]
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and channel_network[nr, nc]:
                    in_degree[nr, nc] -= 1
                    if in_degree[nr, nc] == 0:
                        queue.append((nr, nc))
        return ordered_list

    def route_flows(self, lateral_inflows: np.ndarray):
        """
        Routes water through the channel network for one time step.

        Args:
            lateral_inflows (np.ndarray): Grid of lateral inflows for the current step.

        Returns:
            np.ndarray: Grid of outflows from each channel cell for the current step.
        """
        current_inflow = np.zeros_like(self.fdr, dtype=float)
        current_outflow = np.zeros_like(self.fdr, dtype=float)

        for r, c in self.channel_cells_ordered:
            # Sum inflows from upstream neighbors
            upstream_inflow = 0
            # This requires finding who flows TO (r,c), which is inefficient.
            # Instead, we build the inflow as we iterate.
            # The logic is simpler: I_t is the sum of lateral inflow and upstream outflows.

            # The inflow to this cell is its lateral inflow + the outflow from any upstream cells.
            # The topological sort ensures upstream outflows are already calculated.
            current_inflow[r, c] = lateral_inflows[r, c]

            # Find upstream cells and add their outflow to current_inflow[r,c]
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]:
                 pr, pc = r-dr, c-dc # previous r, c
                 if 0 <= pr < self.fdr.shape[0] and 0 <= pc < self.fdr.shape[1]:
                     if self.channel_network[pr,pc]:
                         direction = self.fdr[pr,pc]
                         if direction in self.d8_to_offset:
                             offset_r, offset_c = self.d8_to_offset[direction]
                             if pr + offset_r == r and pc + offset_c == c:
                                 current_inflow[r,c] += current_outflow[pr,pc]


            # Apply Muskingum equation
            outflow = self.c1 * current_inflow[r, c] + self.c2 * self.prev_inflow[r, c] + self.c3 * self.prev_outflow[r, c]
            current_outflow[r, c] = max(0, outflow)

        # Update state for the next time step
        self.prev_inflow = current_inflow
        self.prev_outflow = current_outflow

        return current_outflow
