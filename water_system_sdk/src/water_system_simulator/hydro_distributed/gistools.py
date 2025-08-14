import numpy as np
from typing import List, Tuple, Dict

class GISTools:
    """
    A collection of tools for DEM and GIS data analysis.
    """

    @staticmethod
    def fill_sinks(dem: np.ndarray, no_data_val: float = -9999) -> np.ndarray:
        """
        Fills sinks in a Digital Elevation Model (DEM) using a priority queue method.
        """
        import heapq

        rows, cols = dem.shape
        filled_dem: np.ndarray = np.copy(dem)
        processed: np.ndarray = np.zeros_like(dem, dtype=bool)
        pq: List[Tuple[float, int, int]] = []

        for r in range(rows):
            for c in range(cols):
                if r == 0 or r == rows - 1 or c == 0 or c == cols - 1:
                    if dem[r, c] != no_data_val:
                        heapq.heappush(pq, (float(dem[r, c]), r, c))
                        processed[r, c] = True

        while pq:
            elev, r, c = heapq.heappop(pq)
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0: continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and not processed[nr, nc]:
                        if filled_dem[nr, nc] != no_data_val:
                            processed[nr, nc] = True
                            new_elev = float(max(filled_dem[nr, nc], elev))
                            filled_dem[nr, nc] = new_elev
                            heapq.heappush(pq, (new_elev, nr, nc))
        return filled_dem

    @staticmethod
    def flow_direction(dem: np.ndarray, no_data_val: float = -9999) -> np.ndarray:
        """
        Calculates D8 flow direction for each cell in a DEM.
        This version processes the entire grid, including borders.
        """
        rows, cols = dem.shape
        fdr: np.ndarray = np.zeros_like(dem, dtype=np.uint8)

        neighbors: List[Tuple[int, int, int]] = [
            (0, 1, 1), (1, 1, 2), (1, 0, 4), (1, -1, 8),
            (0, -1, 16), (-1, -1, 32), (-1, 0, 64), (-1, 1, 128)
        ]

        for r in range(rows):  # Process ALL rows
            for c in range(cols):  # Process ALL columns
                if dem[r, c] == no_data_val:
                    fdr[r, c] = 0
                    continue

                max_slope: float = -np.inf
                direction: int = 0

                for dr, dc, code in neighbors:
                    nr, nc = r + dr, c + dc

                    # Bounds check is crucial here
                    if 0 <= nr < rows and 0 <= nc < cols:
                        if dem[nr, nc] != no_data_val:
                            distance: float = float(np.sqrt(dr**2 + dc**2))
                            slope: float = (float(dem[r, c]) - float(dem[nr, nc])) / distance

                            if slope > max_slope:
                                max_slope = slope
                                direction = code

                if max_slope > 0:
                    fdr[r, c] = direction
                else:
                    # It's a sink or flat area, flow direction is 0 (no flow)
                    fdr[r, c] = 0
        return fdr

    @staticmethod
    def flow_accumulation(fdr: np.ndarray) -> np.ndarray:
        """
        Calculates the flow accumulation for each cell using a topological sort.
        """
        rows, cols = fdr.shape
        fac: np.ndarray = np.ones(fdr.shape, dtype=np.uint32)
        in_degree: np.ndarray = np.zeros(fdr.shape, dtype=np.uint8)

        d8_to_offset: Dict[int, Tuple[int, int]] = {
            1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1),
            16: (0, -1), 32: (-1, -1), 64: (-1, 0), 128: (-1, 1)
        }

        for r in range(rows):
            for c in range(cols):
                direction = int(fdr[r, c])
                if direction in d8_to_offset:
                    dr, dc = d8_to_offset[direction]
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        in_degree[nr, nc] += 1

        queue: List[Tuple[int, int]] = [(r, c) for r in range(rows) for c in range(cols) if in_degree[r, c] == 0]
        head: int = 0
        while head < len(queue):
            r, c = queue[head]
            head += 1

            direction = int(fdr[r, c])
            if direction in d8_to_offset:
                dr, dc = d8_to_offset[direction]
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    fac[nr, nc] += fac[r, c]
                    in_degree[nr, nc] -= 1
                    if in_degree[nr, nc] == 0:
                        queue.append((nr, nc))
        return fac
