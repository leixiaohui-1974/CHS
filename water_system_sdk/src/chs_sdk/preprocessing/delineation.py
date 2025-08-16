import numpy as np
from typing import List, Tuple, Dict
from scipy.ndimage import label

# Correcting the import path based on the file structure
from ..hydro_distributed.gistools import GISTools
from .structures import ParameterZonePreprocessing, SubBasinPreprocessing

class WatershedDelineator:
    """
    A tool to delineate watersheds and sub-basins from a DEM.
    It uses GISTools for basic DEM processing and then implements
    watershed delineation algorithms.
    """

    def __init__(self, dem: np.ndarray, no_data_val: float = -9999):
        """
        Initializes the delineator with the DEM.
        """
        self.dem = dem
        self.no_data_val = no_data_val
        self.rows, self.cols = dem.shape
        self.gis_tools = GISTools()

        self.filled_dem = None
        self.fdr = None
        self.fac = None
        self._downstream_map = None

        self._d8_offsets = {
            1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1),
            16: (0, -1), 32: (-1, -1), 64: (-1, 0), 128: (-1, 1)
        }

    def _preprocess_dem(self, perform_sink_fill=True):
        """
        Performs the basic DEM processing steps.
        Sink filling can be skipped for idealized DEMs.
        """
        if self.filled_dem is None:
            if perform_sink_fill:
                print("Step 1/3: Filling sinks...")
                self.filled_dem = self.gis_tools.fill_sinks(self.dem, self.no_data_val)
            else:
                print("Step 1/3: SKIPPING sink fill for idealized DEM...")
                self.filled_dem = self.dem

        if self.fdr is None:
            print("Step 2/3: Calculating flow direction...")
            self.fdr = self.gis_tools.flow_direction(self.filled_dem, self.no_data_val)
        if self.fac is None:
            print("Step 3/3: Calculating flow accumulation...")
            self.fac = self.gis_tools.flow_accumulation(self.fdr)

    def _get_downstream_map(self) -> Dict[Tuple[int, int], Tuple[int, int]]:
        """Helper to create a dictionary mapping a cell to its downstream neighbor for fast lookup."""
        if self._downstream_map is None:
            self._downstream_map = {}
            for r in range(self.rows):
                for c in range(self.cols):
                    direction = self.fdr[r, c]
                    if direction in self._d8_offsets:
                        dr, dc = self._d8_offsets[direction]
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.rows and 0 <= nc < self.cols:
                            self._downstream_map[(r, c)] = (nr, nc)
        return self._downstream_map

    def delineate_parameter_zones(self, outlet_points: List[Tuple[int, int]], perform_sink_fill=True) -> List[ParameterZonePreprocessing]:
        """Delineates the catchment area (Parameter Zone) for each outlet point."""
        if self.fdr is None:
            # For the synthetic test case, we will disable sink filling.
            # For real-world DEMs, this should be True.
            self._preprocess_dem(perform_sink_fill=perform_sink_fill)

        zones = []
        for i, (r_out, c_out) in enumerate(outlet_points):
            print(f"Delineating zone for outlet at ({r_out}, {c_out})...")
            mask = np.zeros_like(self.dem, dtype=bool)
            q = [(r_out, c_out)]
            mask[r_out, c_out] = True

            head = 0
            while head < len(q):
                r, c = q[head]
                head += 1
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0: continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.rows and 0 <= nc < self.cols and not mask[nr, nc]:
                            flow_dir_neighbor = self.fdr[nr, nc]
                            if flow_dir_neighbor in self._d8_offsets:
                                offset_r, offset_c = self._d8_offsets[flow_dir_neighbor]
                                if nr + offset_r == r and nc + offset_c == c:
                                    mask[nr, nc] = True
                                    q.append((nr, nc))

            zone = ParameterZonePreprocessing(id=f"P{i+1:02d}", mask=mask, observation_point=(r_out, c_out))
            zones.append(zone)
            print(f"Zone {zone.id} delineated with {np.sum(mask)} cells.")
        return zones

    def delineate_sub_basins(self, zones: List[ParameterZonePreprocessing], stream_threshold: int) -> List[ParameterZonePreprocessing]:
        """Delineates sub-basins within each Parameter Zone based on a stream network."""
        if self.fac is None: self._preprocess_dem()

        print(f"\nStarting sub-basin delineation with stream threshold: {stream_threshold}...")
        stream_mask = self.fac >= stream_threshold
        stream_segments, num_segments = label(stream_mask)
        print(f"Identified {num_segments} potential stream segments globally.")

        flow_to = self._get_downstream_map()
        sub_basin_map = np.zeros_like(self.dem, dtype=np.int32)

        for zone in zones:
            print(f"Processing zone: {zone.id}")
            zone_rows, zone_cols = np.where(zone.mask)

            zone_stream_segments = stream_segments[zone.mask]
            unique_zone_segment_ids = np.unique(zone_stream_segments[zone_stream_segments != 0])
            print(f"Found {len(unique_zone_segment_ids)} stream segments in zone {zone.id}.")

            for r, c in zip(zone_rows, zone_cols):
                if sub_basin_map[r, c] != 0: continue

                path = []
                curr_r, curr_c = r, c

                while True:
                    if not (0 <= curr_r < self.rows and 0 <= curr_c < self.cols):
                        basin_id = 0; break

                    if sub_basin_map[curr_r, curr_c] > 0:
                        basin_id = sub_basin_map[curr_r, curr_c]; break

                    if stream_segments[curr_r, curr_c] > 0:
                        basin_id = stream_segments[curr_r, curr_c]; break

                    path.append((curr_r, curr_c))
                    next_pos = flow_to.get((curr_r, curr_c))

                    if next_pos is None:
                        basin_id = 0; break
                    curr_r, curr_c = next_pos

                for path_r, path_c in path:
                    sub_basin_map[path_r, path_c] = basin_id

            sub_basin_count = 0
            for segment_id in unique_zone_segment_ids:
                sub_basin_count += 1
                mask = (sub_basin_map == segment_id) & zone.mask
                if np.any(mask):
                    sub_basin = SubBasinPreprocessing(id=f"{zone.id}-S{sub_basin_count:02d}", mask=mask)
                    zone.sub_basins.append(sub_basin)

            print(f"Delineated {len(zone.sub_basins)} sub-basins in zone {zone.id}.")

        return zones
