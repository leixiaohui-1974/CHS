import numpy as np
import logging
from typing import Optional
# Use a relative import to access the mesh module within the same package
from .mesh import UnstructuredMesh

logger = logging.getLogger(__name__)

class GPUDataManager: # Note: Class name is now a misnomer, but we keep it for consistency with the plan.
    """
    Manages the state variables of the hydrodynamic simulation on the CPU.

    This class holds all the dynamic (e.g., water depth) and static (e.g.,
    bed elevation) variables required for the solver, stored as NumPy arrays.
    """

    def __init__(self, mesh: UnstructuredMesh, manning_n: float = 0.03, initial_h: float = 0.01, bed_elevation: Optional[np.ndarray] = None):
        """
        Initializes the data manager and allocates memory for state variables.

        Args:
            mesh (UnstructuredMesh): The computational mesh object.
            manning_n (float or np.ndarray): The Manning's roughness coefficient.
            initial_h (float): The initial water depth across the domain.
            bed_elevation (np.ndarray, optional): Array of bed elevations for each cell.
        """
        logger.info("Initializing DataManager for CPU...")
        self.mesh = mesh
        num_cells = self.mesh.num_cells

        # --- Static variables (mesh properties) ---
        self.z: np.ndarray
        if bed_elevation is None:
            self.z = np.zeros(num_cells, dtype=np.float64)
        else:
            if not isinstance(bed_elevation, np.ndarray) or bed_elevation.shape[0] != num_cells:
                raise ValueError("bed_elevation must be a NumPy array with a shape matching the number of cells.")
            self.z = bed_elevation

        if isinstance(manning_n, (float, int)):
            self.n = np.full(num_cells, manning_n, dtype=np.float64)
        else:
            if not isinstance(manning_n, np.ndarray) or manning_n.shape[0] != num_cells:
                raise ValueError("manning_n must be a float or a NumPy array with a shape matching the number of cells.")
            self.n = manning_n

        # --- Dynamic variables (state variables) ---

        self.h = np.full(num_cells, initial_h, dtype=np.float64)
        self.h = np.maximum(self.h, 0.0)

        self.hu = np.zeros(num_cells, dtype=np.float64)
        self.hv = np.zeros(num_cells, dtype=np.float64)

        # --- Derived quantities ---
        self.wse = self.z + self.h

        # --- Source Term variables ---
        self.source_terms = np.zeros((num_cells, 3), dtype=np.float64)

        logger.info("DataManager initialized successfully.")

    def update_wse(self):
        """Updates the water surface elevation based on the current water depth."""
        self.wse = self.z + self.h
