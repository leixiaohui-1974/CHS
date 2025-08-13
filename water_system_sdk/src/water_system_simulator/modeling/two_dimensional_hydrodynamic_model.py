import numpy as np

from .base_model import BaseModel
from ..hydrodynamics_2d.mesh import load_mesh, UnstructuredMesh
from ..hydrodynamics_2d.data_manager import GPUDataManager
from ..hydrodynamics_2d.solver import Solver

class TwoDimensionalHydrodynamicModel(BaseModel):
    """
    A high-level wrapper for the 2D St. Venant equation solver on unstructured meshes.
    This model can be integrated into the CHS SDK SimulationManager.
    """
    def __init__(self, mesh_file: str, manning_n: float = 0.03, initial_h: float = 0.01,
                 cfl: float = 0.5, coupling_boundaries: dict = None, bed_elevation: np.ndarray = None, **kwargs):
        """
        Initializes the 2D hydrodynamic model.
        """
        super().__init__()
        print(f"Initializing TwoDimensionalHydrodynamicModel from mesh: {mesh_file}")

        points, cells = load_mesh(mesh_file)

        self.mesh = UnstructuredMesh(points, cells)
        self.data_manager = GPUDataManager(self.mesh, manning_n=manning_n, initial_h=initial_h, bed_elevation=bed_elevation)
        self.solver = Solver(self.data_manager, cfl=cfl) # cfl is now passed to solver but not used there, can be removed later.

        self.current_time = 0.0
        self.cfl_number = cfl
        self.dry_tolerance = 1e-6

        self.boundary_name_to_cell_indices = {}
        if coupling_boundaries:
            self._setup_coupling_boundaries(coupling_boundaries)

        print("TwoDimensionalHydrodynamicModel initialized successfully.")

    def _setup_coupling_boundaries(self, boundaries_config: dict):
        print("Processing coupling boundaries...")
        for name, cell_indices in boundaries_config.items():
            self.boundary_name_to_cell_indices[name] = np.asarray(cell_indices, dtype=np.int32)
            print(f"  - Registered boundary '{name}' with {len(cell_indices)} cells.")

    def _calculate_cfl_dt(self):
        """
        Calculates the maximum stable time step (dt) based on the CFL condition.
        """
        dm = self.data_manager
        mesh = dm.mesh
        h_eff = dm.h + self.dry_tolerance
        u = dm.hu / h_eff
        v = dm.hv / h_eff
        velocity_mag = np.sqrt(u**2 + v**2)
        celerity = np.sqrt(self.solver.g * dm.h)
        char_length = np.sqrt(mesh.cell_areas)
        wave_speed = np.maximum(velocity_mag + celerity, self.dry_tolerance)
        local_dt = char_length / wave_speed
        global_dt = np.min(local_dt)
        # Handle case where domain is totally dry and still
        if np.isinf(global_dt):
            return 1.0 # Return a default dt if no wave speed
        return self.cfl_number * float(global_dt)

    def step(self, dt: float, t: float = 0):
        """
        Advances the simulation by a fixed duration `dt` by taking multiple
        smaller, stable internal steps (sub-stepping).
        """
        time_to_simulate = dt
        time_simulated = 0.0

        while time_simulated < time_to_simulate:
            internal_dt = self._calculate_cfl_dt()

            # Ensure we don't overstep the main time window
            internal_dt = min(internal_dt, time_to_simulate - time_simulated)

            # If dt is zero or negative, we can't proceed.
            if internal_dt <= 0:
                break

            self.solver.step(internal_dt)

            time_simulated += internal_dt
            self.current_time += internal_dt

        self.output = self.get_state()
        self.data_manager.source_terms.fill(0)
        return dt

    def get_state(self):
        dm = self.data_manager
        total_volume = float(np.sum(dm.h * dm.mesh.cell_areas))
        max_water_depth = float(np.max(dm.h))
        return {
            "time": self.current_time,
            "total_volume_m3": total_volume,
            "max_water_depth_m": max_water_depth,
        }

    def get_coupling_boundary_water_level(self, boundary_name: str) -> float:
        if boundary_name not in self.boundary_name_to_cell_indices:
            raise ValueError(f"Coupling boundary '{boundary_name}' not found.")
        cell_indices = self.boundary_name_to_cell_indices[boundary_name]
        wse = self.data_manager.wse[cell_indices]
        areas = self.mesh.cell_areas[cell_indices]
        total_area = np.sum(areas)
        if total_area < 1e-9: return 0.0
        weighted_wse = np.sum(wse * areas) / total_area
        return float(weighted_wse)

    def set_coupling_boundary_flow(self, boundary_name: str, flow: float):
        if boundary_name not in self.boundary_name_to_cell_indices:
            raise ValueError(f"Coupling boundary '{boundary_name}' not found.")
        cell_indices = self.boundary_name_to_cell_indices[boundary_name]
        if len(cell_indices) == 0: return
        areas = self.mesh.cell_areas[cell_indices]
        total_area = np.sum(areas)
        if total_area > 1e-9:
            distributed_flow = flow * (areas / total_area)
            np.add.at(self.data_manager.source_terms, (cell_indices, 0), distributed_flow)
