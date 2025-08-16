import numpy as np
from typing import List, Dict, Any

from .structures import ParameterZonePreprocessing, SubBasinPreprocessing

class ParameterExtractor:
    """
    A tool to extract physical and model-specific parameters for each sub-basin,
    based on GIS data layers.
    """

    def __init__(self,
                 dem: np.ndarray,
                 land_use: np.ndarray,
                 soil_type: np.ndarray,
                 cell_size_m: float,
                 no_data_val: float = -9999):
        """
        Initializes the extractor with all necessary GIS data.

        Args:
            dem (np.ndarray): The Digital Elevation Model grid.
            land_use (np.ndarray): The land use grid.
            soil_type (np.ndarray): The soil type grid.
            cell_size_m (float): The size of each grid cell in meters.
            no_data_val (float): The value representing no data.
        """
        self.dem = dem
        self.land_use = land_use
        self.soil_type = soil_type
        self.cell_size_m = cell_size_m
        self.cell_area_sqkm = (cell_size_m ** 2) / 1_000_000
        self.no_data_val = no_data_val
        self.slope_grid = self._calculate_slope()

        # A sample lookup table for SCS Curve Number.
        # In a real application, this would be much larger and configurable.
        # Format: {(land_use_code, soil_hydro_group_code): curve_number}
        # Soil hydro groups (A, B, C, D) are typically coded as 1, 2, 3, 4.
        self.cn_lookup_table = {
            (10, 1): 30, (10, 2): 55, (10, 3): 70, (10, 4): 77,  # e.g., 10=Forest
            (20, 1): 40, (20, 2): 60, (20, 3): 74, (20, 4): 80,  # e.g., 20=Pasture
            (30, 1): 62, (30, 2): 75, (30, 3): 83, (30, 4): 87,  # e.g., 30=Agriculture
            (40, 1): 98, (40, 2): 98, (40, 3): 98, (40, 4): 98,  # e.g., 40=Urban/Impervious
        }

    def _calculate_slope(self) -> np.ndarray:
        """Calculates the slope for the entire DEM in degrees using numpy.gradient."""
        grad_y, grad_x = np.gradient(self.dem, self.cell_size_m)
        slope_rad = np.arctan(np.sqrt(grad_x**2 + grad_y**2))
        return np.degrees(slope_rad)

    def extract_all_parameters(self, zones: List[ParameterZonePreprocessing]) -> List[ParameterZonePreprocessing]:
        """
        Main method to orchestrate parameter extraction for all zones and sub-basins.
        """
        print("\nStarting parameter extraction...")
        for zone in zones:
            print(f"Extracting parameters for zone: {zone.id}")
            if not zone.sub_basins:
                print(f"  - WARNING: No sub-basins found for zone {zone.id}. Skipping.")
                continue
            for sub_basin in zone.sub_basins:
                print(f"  - Sub-basin: {sub_basin.id}")
                self._calculate_physical_parameters(sub_basin)
                self._generate_model_parameters(sub_basin)
        print("Parameter extraction complete.")
        return zones

    def _calculate_physical_parameters(self, sub_basin: SubBasinPreprocessing):
        """Calculates and stores physical parameters for a sub-basin."""
        mask = sub_basin.mask

        # Area
        num_cells = np.sum(mask)
        sub_basin.area_sqkm = num_cells * self.cell_area_sqkm

        # Average Slope
        slopes_in_basin = self.slope_grid[mask]
        sub_basin.avg_slope = np.mean(slopes_in_basin) if slopes_in_basin.size > 0 else 0

        sub_basin.physical_parameters['area_sqkm'] = sub_basin.area_sqkm
        sub_basin.physical_parameters['avg_slope_deg'] = sub_basin.avg_slope

        print(f"    - Physical Params: Area={sub_basin.area_sqkm:.2f} sqkm, Slope={sub_basin.avg_slope:.2f} deg")

    def _generate_model_parameters(self, sub_basin: SubBasinPreprocessing):
        """Calculates and stores model-specific parameters."""

        # --- SCS Curve Number ---
        cn = self._get_scs_curve_number(sub_basin.mask)
        sub_basin.model_parameters['scs_curve_number'] = cn

        # --- Unit Hydrograph (Placeholder) ---
        # In a real implementation, this would use empirical formulas based on physical params
        # such as time of concentration, which depends on longest flow path and slope.
        uh_tp = 2.0 * (sub_basin.avg_slope**-0.5) if sub_basin.avg_slope > 0.1 else 10.0 # Simplistic placeholder
        sub_basin.model_parameters['uh_time_to_peak_hr'] = uh_tp

        print(f"    - Model Params: SCS_CN={cn:.2f}, UH_Tp={uh_tp:.2f} hr")

    def _get_scs_curve_number(self, mask: np.ndarray) -> float:
        """Calculates the area-weighted average SCS Curve Number for a given mask."""
        if not np.any(mask): return 70.0 # Default CN for empty masks

        lu_in_basin = self.land_use[mask]
        st_in_basin = self.soil_type[mask]

        # Find unique combinations of land use and soil type and their counts
        unique_combos, counts = np.unique(np.vstack([lu_in_basin, st_in_basin]), axis=1, return_counts=True)

        total_area_cells = np.sum(counts)
        if total_area_cells == 0: return 70.0 # Default CN

        weighted_cn_sum = 0
        for i in range(unique_combos.shape[1]):
            lu_code = unique_combos[0, i]
            st_code = unique_combos[1, i]
            count = counts[i]

            # Get CN from lookup table, use a default if not found
            cn = self.cn_lookup_table.get((lu_code, st_code), 70)
            weighted_cn_sum += cn * count

        return weighted_cn_sum / total_area_cells
