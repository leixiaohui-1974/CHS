import numpy as np

from .data_manager import GPUDataManager

def _calculate_hllc_flux(h_l, hu_l, hv_l, z_l, h_r, hu_r, hv_r, z_r, nx, ny, g, dry_tol):
    """
    NumPy-based HLLC Approximate Riemann Solver for 2D Shallow Water Equations.
    This is a vectorized function that computes fluxes for all edges at once.
    """
    # A. PREPARE ROTATED STATES
    u_l = np.divide(hu_l, h_l, out=np.zeros_like(hu_l), where=h_l > dry_tol)
    v_l = np.divide(hv_l, h_l, out=np.zeros_like(hv_l), where=h_l > dry_tol)
    u_r = np.divide(hu_r, h_r, out=np.zeros_like(hu_r), where=h_r > dry_tol)
    v_r = np.divide(hv_r, h_r, out=np.zeros_like(hv_r), where=h_r > dry_tol)

    un_l = u_l * nx + v_l * ny
    ut_l = -u_l * ny + v_l * nx
    un_r = u_r * nx + v_r * ny
    ut_r = -u_r * ny + v_r * nx

    a_l = np.sqrt(g * h_l)
    a_r = np.sqrt(g * h_r)

    # B. COMPUTE WAVE SPEEDS (HLL)
    h_roe = 0.5 * (h_l + h_r)
    sqrt_h_l = np.sqrt(h_l)
    sqrt_h_r = np.sqrt(h_r)
    u_roe = (un_l * sqrt_h_l + un_r * sqrt_h_r) / (sqrt_h_l + sqrt_h_r + dry_tol)
    a_roe = np.sqrt(g * h_roe)

    s_l = np.minimum(un_l - a_l, u_roe - a_roe)
    s_r = np.maximum(un_r + a_r, u_roe + a_roe)

    # C. COMPUTE STAR REGION SPEED (HLLC)
    p_l = 0.5 * g * h_l * h_l
    p_r = 0.5 * g * h_r * h_r

    s_star_denom = (h_r * (un_r - s_r) - h_l * (un_l - s_l))
    s_star = (p_l - p_r + h_r * un_r * (un_r - s_r) - h_l * un_l * (un_l - s_l)) / (s_star_denom + dry_tol)

    # D. COMPUTE HLLC FLUX
    f_h_l = h_l * un_l
    f_hun_l = f_h_l * un_l + p_l
    f_hut_l = f_h_l * ut_l

    f_h_r = h_r * un_r
    f_hun_r = f_h_r * un_r + p_r
    f_hut_r = f_h_r * ut_r

    cond_l = (0 <= s_l)
    cond_r = (s_r <= 0)
    cond_star_l = (s_l < 0) & (0 <= s_star)

    h_star_l = h_l * (s_l - un_l) / (s_l - s_star + dry_tol)
    f_h_sl = f_h_l + s_l * (h_star_l - h_l)
    f_hun_sl = f_hun_l + s_l * (h_star_l * s_star - h_l * un_l)
    f_hut_sl = f_hut_l + s_l * (h_star_l * ut_l - h_l * ut_l)

    h_star_r = h_r * (s_r - un_r) / (s_r - s_star + dry_tol)
    f_h_sr = f_h_r + s_r * (h_star_r - h_r)
    f_hun_sr = f_hun_r + s_r * (h_star_r * s_star - h_r * un_r)
    f_hut_sr = f_hut_r + s_r * (h_star_r * ut_r - h_r * ut_r)

    f_h = np.select([cond_l, cond_r, cond_star_l], [f_h_l, f_h_r, f_h_sl], default=f_h_sr)
    f_hun = np.select([cond_l, cond_r, cond_star_l], [f_hun_l, f_hun_r, f_hun_sl], default=f_hun_sr)
    f_hut = np.select([cond_l, cond_r, cond_star_l], [f_hut_l, f_hut_r, f_hut_sl], default=f_hut_sr)

    # E. ROTATE FLUX BACK
    flux_h = f_h
    flux_hu = f_hun * nx - f_hut * ny
    flux_hv = f_hun * ny + f_hut * nx

    return flux_h, flux_hu, flux_hv

class Solver:
    def __init__(self, data_manager: GPUDataManager, g: float = 9.81, cfl: float = 0.5):
        self.data_manager = data_manager
        self.g = g
        self.cfl_number = cfl
        self.dry_tolerance = 1e-6

    def _calculate_fluxes(self):
        dm = self.data_manager
        mesh = dm.mesh
        cell_l_idx = mesh.edge_to_cell[:, 0]
        cell_r_idx = mesh.edge_to_cell[:, 1]

        h_l, hu_l, hv_l, z_l = dm.h[cell_l_idx], dm.hu[cell_l_idx], dm.hv[cell_l_idx], dm.z[cell_l_idx]
        h_r, hu_r, hv_r, z_r = dm.h[cell_r_idx], dm.hu[cell_r_idx], dm.hv[cell_r_idx], dm.z[cell_r_idx]

        boundary_mask = cell_r_idx < 0
        h_r[boundary_mask] = h_l[boundary_mask]
        z_r[boundary_mask] = z_l[boundary_mask]

        h_l_b = h_l[boundary_mask] + self.dry_tolerance
        u_l_b, v_l_b = hu_l[boundary_mask] / h_l_b, hv_l[boundary_mask] / h_l_b
        nx_b, ny_b = mesh.edge_normals[boundary_mask, 0], mesh.edge_normals[boundary_mask, 1]

        un_l_b = u_l_b * nx_b + v_l_b * ny_b
        ut_l_b = -u_l_b * ny_b + v_l_b * nx_b
        un_r_b, ut_r_b = -un_l_b, ut_l_b

        u_r_b = un_r_b * nx_b - ut_r_b * ny_b
        v_r_b = un_r_b * ny_b + ut_r_b * nx_b

        hu_r[boundary_mask] = u_r_b * h_r[boundary_mask]
        hv_r[boundary_mask] = v_r_b * h_r[boundary_mask]

        flux_h, flux_hu, flux_hv = _calculate_hllc_flux(
            h_l, hu_l, hv_l, z_l, h_r, hu_r, hv_r, z_r,
            mesh.edge_normals[:, 0], mesh.edge_normals[:, 1],
            self.g, self.dry_tolerance
        )

        # For perfect conservation, explicitly enforce zero mass flux at solid boundaries.
        # The momentum flux represents the pressure force against the wall.
        flux_h[boundary_mask] = 0.0

        fluxes = np.vstack([flux_h, flux_hu, flux_hv]).T
        fluxes *= mesh.edge_lengths[:, np.newaxis]
        return fluxes

    def _update_state(self, fluxes, dt):
        dm = self.data_manager
        mesh = dm.mesh
        net_flux_per_cell = np.zeros((mesh.num_cells, 3), dtype=np.float64)
        cell_l = mesh.edge_to_cell[:, 0]
        cell_r = mesh.edge_to_cell[:, 1]

        np.add.at(net_flux_per_cell, cell_l, -fluxes)
        internal_edges_mask = cell_r >= 0
        np.add.at(net_flux_per_cell, cell_r[internal_edges_mask], fluxes[internal_edges_mask])

        source_term = np.zeros_like(net_flux_per_cell)
        h_eff = dm.h + self.dry_tolerance
        u, v = dm.hu / h_eff, dm.hv / h_eff
        velocity_mag = np.sqrt(u**2 + v**2)
        n_sq = dm.n**2
        friction_denom = h_eff**(4./3.)

        s_fx = -self.g * n_sq * u * velocity_mag / friction_denom
        s_fy = -self.g * n_sq * v * velocity_mag / friction_denom
        source_term[:, 1], source_term[:, 2] = s_fx, s_fy

        update_from_flux = (dt / mesh.cell_areas[:, np.newaxis]) * (net_flux_per_cell + dm.source_terms)
        update_from_friction = dt * source_term
        dm.h += update_from_flux[:, 0]
        dm.hu += update_from_flux[:, 1] + update_from_friction[:, 1]
        dm.hv += update_from_flux[:, 2] + update_from_friction[:, 2]

        dm.h = np.maximum(dm.h, 0.0)
        dry_mask = dm.h < self.dry_tolerance
        dm.hu[dry_mask], dm.hv[dry_mask] = 0.0, 0.0

    def step(self, dt: float):
        """
        Performs a single, complete time step of the simulation with a given dt.
        """
        fluxes = self._calculate_fluxes()
        self._update_state(fluxes, dt)
        self.data_manager.update_wse()
