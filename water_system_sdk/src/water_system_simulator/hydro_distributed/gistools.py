import numpy as np

class GISTools:
    """
    A collection of tools for DEM and GIS data analysis.
    """

    @staticmethod
    def fill_sinks(dem: np.ndarray, no_data_val: float = -9999):
        """
        Fills sinks in a Digital Elevation Model (DEM) using a priority queue method.

        This algorithm floods the DEM from the edges, filling depressions to their
        pour point elevation.

        Args:
            dem (np.ndarray): The input DEM grid.
            no_data_val (float): The value representing no data in the DEM.

        Returns:
            np.ndarray: The DEM with sinks filled.
        """
        import heapq

        rows, cols = dem.shape
        filled_dem = np.copy(dem)
        processed = np.zeros_like(dem, dtype=bool)

        # Priority queue stores (elevation, r, c)
        pq = []

        # Initialize the queue with all edge cells
        for r in range(rows):
            for c in range(cols):
                if r == 0 or r == rows - 1 or c == 0 or c == cols - 1:
                    if dem[r, c] != no_data_val:
                        heapq.heappush(pq, (dem[r, c], r, c))
                        processed[r, c] = True

        # Process cells from the queue
        while pq:
            elev, r, c = heapq.heappop(pq)

            # For each neighbor
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue

                    nr, nc = r + dr, c + dc

                    if 0 <= nr < rows and 0 <= nc < cols and not processed[nr, nc]:
                        if filled_dem[nr, nc] != no_data_val:
                            processed[nr, nc] = True

                            # If neighbor is lower, raise it to current cell's elevation
                            new_elev = max(filled_dem[nr, nc], elev)
                            filled_dem[nr, nc] = new_elev
                            heapq.heappush(pq, (new_elev, nr, nc))

        return filled_dem

    @staticmethod
    def flow_direction(dem: np.ndarray):
        """
        Calculates D8 flow direction for each cell in a DEM.

        Uses the standard D8 convention where flow directions are encoded as:
        32  64  128
        16   0    1
        8   4    2

        Args:
            dem (np.ndarray): The input DEM grid. A no-data value (e.g., -9999) is expected.

        Returns:
            np.ndarray: A grid of flow directions.
        """
        rows, cols = dem.shape
        fdr = np.zeros_like(dem, dtype=np.uint8)
        no_data_val = -9999  # A common no-data value

        # Define the 8 neighbors' relative positions and D8 codes
        # (row_offset, col_offset, D8_code)
        neighbors = [
            (0, 1, 1),    # East
            (1, 1, 2),    # South-East
            (1, 0, 4),    # South
            (1, -1, 8),   # South-West
            (0, -1, 16),  # West
            (-1, -1, 32), # North-West
            (-1, 0, 64),  # North
            (-1, 1, 128)  # North-East
        ]

        for r in range(1, rows - 1):
            for c in range(1, cols - 1):
                if dem[r, c] == no_data_val:
                    fdr[r, c] = 0  # Or a specific no-data value for flow direction
                    continue

                max_slope = -np.inf
                direction = 0

                for dr, dc, code in neighbors:
                    nr, nc = r + dr, c + dc
                    if dem[nr, nc] != no_data_val:
                        # Calculate slope
                        distance = np.sqrt(dr**2 + dc**2)
                        slope = (dem[r, c] - dem[nr, nc]) / distance

                        if slope > max_slope:
                            max_slope = slope
                            direction = code

                if max_slope > 0:
                    fdr[r, c] = direction
                else:
                    # It's a sink or flat area, flow direction is 0
                    fdr[r, c] = 0

        return fdr

    @staticmethod
    def flow_accumulation(fdr: np.ndarray):
        """
        Calculates the flow accumulation for each cell using a topological sort.

        Args:
            fdr (np.ndarray): The grid of D8 flow directions.

        Returns:
            np.ndarray: A grid of flow accumulation values (number of upstream cells).
        """
        rows, cols = fdr.shape
        fac = np.ones(fdr.shape, dtype=np.uint32)  # Each cell contributes 1 to itself
        in_degree = np.zeros(fdr.shape, dtype=np.uint8)

        # Map D8 codes to (dr, dc) offsets
        d8_to_offset = {
            1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1),
            16: (0, -1), 32: (-1, -1), 64: (-1, 0), 128: (-1, 1)
        }

        # Calculate in-degrees for each cell
        for r in range(rows):
            for c in range(cols):
                direction = fdr[r, c]
                if direction in d8_to_offset:
                    dr, dc = d8_to_offset[direction]
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        in_degree[nr, nc] += 1

        # Initialize queue with cells having an in-degree of 0 (ridges)
        queue = [(r, c) for r in range(rows) for c in range(cols) if in_degree[r, c] == 0]

        head = 0
        while head < len(queue):
            r, c = queue[head]
            head += 1

            direction = fdr[r, c]
            if direction in d8_to_offset:
                dr, dc = d8_to_offset[direction]
                nr, nc = r + dr, c + dc

                if 0 <= nr < rows and 0 <= nc < cols:
                    fac[nr, nc] += fac[r, c]
                    in_degree[nr, nc] -= 1
                    if in_degree[nr, nc] == 0:
                        queue.append((nr, nc))

        return fac
