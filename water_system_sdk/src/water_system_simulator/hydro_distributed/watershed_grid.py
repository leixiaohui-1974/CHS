import numpy as np

class WatershedGrid:
    """
    A container for all spatial raster data for the watershed.

    This class holds and manages grid data (e.g., DEM, flow direction)
    as NumPy arrays.
    """
    def __init__(self, dem_path):
        """
        Initializes the WatershedGrid from a DEM file.

        Args:
            dem_path (str): The file path to the Digital Elevation Model.
        """
        # Note: rasterio will be used here later to load the data
        self.dem = None
        self.flow_direction = None
        self.flow_accumulation = None
        self.slope = None
        self.aspect = None

        # Placeholder for metadata
        self.metadata = {}

    def _load_dem(self, dem_path):
        """Loads the DEM from a file using rasterio."""
        # This will be implemented later.
        pass
