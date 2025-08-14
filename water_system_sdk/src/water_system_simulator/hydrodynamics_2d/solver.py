import numpy as np
from numba import njit

from .data_manager import GPUDataManager

@njit
def _calculate_hllc_flux(h_l, hu_l, hv_l, z_l, h_r, hu_r, hv_r, z_r, nx, ny, g, dry_tol):
    """
    NumPy-based HLLC Approximate Riemann Solver for 2D Shallow Water Equations.
    This is a vectorized function that computes fluxes for all edges at once.
    """
    # A. PREPARE ROTATED STATES
    # Numba-friendly safe division
    u_l = np.zeros_like(h_l)
    v_l = np.zeros_like(h_l)
    u_r = np.zeros_like(h_r)
    v_r = np.zeros_like(h_r)

    for i in range(len(h_l)):
        if h_l[i] > dry_tol:
            u_l[i] = hu_l[i] / h_l[i]
            v_l[i] = hv_l[i] / h_l[i]

    for i in range(len(h_r)):
        if h_r[i] > dry_tol:
            u_r[i] = hu_r[i] / h_r[i]
            v_r[i] = hv_r[i] / h_r[i]

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

    # Numba-compatible equivalent of np.select with array default
    f_h = np.where(cond_l, f_h_l, np.where(cond_r, f_h_r, np.where(cond_star_l, f_h_sl, f_h_sr)))
    f_hun = np.where(cond_l, f_hun_l, np.where(cond_r, f_hun_r, np.where(cond_star_l, f_hun_sl, f_hun_sr)))
    f_hut = np.where(cond_l, f_hut_l, np.where(cond_r, f_hut_r, np.where(cond_star_l, f_hut_sl, f_hut_sr)))

    # E. ROTATE FLUX BACK
    flux_h = f_h
    flux_hu = f_hun * nx - f_hut * ny
    flux_hv = f_hun * ny + f_hut * nx

    return flux_h, flux_hu, flux_hv

@njit
def _compute_fluxes_jitted(h, hu, hv, z, edge_to_cell, edge_normals, edge_lengths, g, dry_tol):
    cell_l_idx = edge_to_cell[:, 0]
    cell_r_idx = edge_to_cell[:, 1]

    # Create copies to avoid modifying source arrays directly in the caller
    h_l, hu_l, hv_l, z_l = h[cell_l_idx], hu[cell_l_idx], hv[cell_l_idx], z[cell_l_idx]
    h_r, hu_r, hv_r, z_r = h[cell_r_idx].copy(), hu[cell_r_idx].copy(), hv[cell_r_idx].copy(), z[cell_r_idx].copy()

    boundary_mask = cell_r_idx < 0
    h_r[boundary_mask] = h_l[boundary_mask]
    z_r[boundary_mask] = z_l[boundary_mask]

    h_l_b = h_l[boundary_mask] + dry_tol
    # Numba doesn't have `divide` with `where`, so we handle it manually
    u_l_b = np.zeros_like(h_l_b)
    v_l_b = np.zeros_like(h_l_b)
    for i in range(len(h_l_b)):
        if h_l_b[i] > dry_tol:
            u_l_b[i] = hu_l[boundary_mask][i] / h_l_b[i]
            v_l_b[i] = hv_l[boundary_mask][i] / h_l_b[i]

    nx_b, ny_b = edge_normals[boundary_mask, 0], edge_normals[boundary_mask, 1]

    un_l_b = u_l_b * nx_b + v_l_b * ny_b
    ut_l_b = -u_l_b * ny_b + v_l_b * nx_b
    un_r_b, ut_r_b = -un_l_b, ut_l_b

    u_r_b = un_r_b * nx_b - ut_r_b * ny_b
    v_r_b = un_r_b * ny_b + ut_r_b * nx_b

    hu_r[boundary_mask] = u_r_b * h_r[boundary_mask]
    hv_r[boundary_mask] = v_r_b * h_r[boundary_mask]

    flux_h, flux_hu, flux_hv = _calculate_hllc_flux(
        h_l, hu_l, hv_l, z_l, h_r, hu_r, hv_r, z_r,
        edge_normals[:, 0], edge_normals[:, 1], g, dry_tol
    )

    flux_h[boundary_mask] = 0.0

    num_edges = len(flux_h)
    fluxes = np.empty((num_edges, 3), dtype=flux_h.dtype)
    fluxes[:, 0] = flux_h
    fluxes[:, 1] = flux_hu
    fluxes[:, 2] = flux_hv

    fluxes *= edge_lengths.reshape(-1, 1)
    return fluxes

@njit
def _update_state_jitted(h, hu, hv, source_terms, n, fluxes, dt, edge_to_cell, cell_areas, g, dry_tol):
    num_cells = len(h)
    net_flux_per_cell = np.zeros((num_cells, 3), dtype=h.dtype)
    cell_l = edge_to_cell[:, 0]
    cell_r = edge_to_cell[:, 1]

    # Numba-friendly explicit loop for flux accumulation
    for i in range(len(edge_to_cell)):
        # Subtract flux from the left cell
        left_cell_idx = cell_l[i]
        net_flux_per_cell[left_cell_idx, 0] -= fluxes[i, 0]
        net_flux_per_cell[left_cell_idx, 1] -= fluxes[i, 1]
        net_flux_per_cell[left_cell_idx, 2] -= fluxes[i, 2]

        # Add flux to the right cell if it's an internal edge
        right_cell_idx = cell_r[i]
        if right_cell_idx >= 0:
            net_flux_per_cell[right_cell_idx, 0] += fluxes[i, 0]
            net_flux_per_cell[right_cell_idx, 1] += fluxes[i, 1]
            net_flux_per_cell[right_cell_idx, 2] += fluxes[i, 2]


    source_term = np.zeros_like(net_flux_per_cell)
    h_eff = h + dry_tol

    # Manual loop for safe division
    u = np.zeros_like(h)
    v = np.zeros_like(h)
    for i in range(len(h_eff)):
        if h_eff[i] > dry_tol:
            u[i] = hu[i] / h_eff[i]
            v[i] = hv[i] / h_eff[i]

    velocity_mag = np.sqrt(u**2 + v**2)
    n_sq = n**2
    friction_denom = h_eff**(4./3.)

    # Manual loop for safe division
    s_fx = np.zeros_like(h)
    s_fy = np.zeros_like(h)
    for i in range(len(friction_denom)):
        if friction_denom[i] > dry_tol:
            s_fx[i] = -g * n_sq[i] * u[i] * velocity_mag[i] / friction_denom[i]
            s_fy[i] = -g * n_sq[i] * v[i] * velocity_mag[i] / friction_denom[i]

    source_term[:, 1], source_term[:, 2] = s_fx, s_fy

    update_from_flux = (dt / cell_areas.reshape(-1, 1)) * (net_flux_per_cell + source_terms)
    update_from_friction = dt * source_term
    h += update_from_flux[:, 0]
    hu += update_from_flux[:, 1] + update_from_friction[:, 1]
    hv += update_from_flux[:, 2] + update_from_friction[:, 2]

    for i in range(len(h)):
        if h[i] < dry_tol:
            h[i] = 0.0
            hu[i] = 0.0
            hv[i] = 0.0

class Solver:
    def __init__(self, data_manager: GPUDataManager, g: float = 9.81, cfl: float = 0.5):
        self.data_manager = data_manager
        self.g = g
        self.cfl_number = cfl
        self.dry_tolerance = 1e-6

    def _calculate_fluxes(self):
        dm = self.data_manager
        mesh = dm.mesh
        return _compute_fluxes_jitted(
            dm.h, dm.hu, dm.hv, dm.z,
            mesh.edge_to_cell, mesh.edge_normals, mesh.edge_lengths,
            self.g, self.dry_tolerance
        )

    def _update_state(self, fluxes, dt):
        dm = self.data_manager
        mesh = dm.mesh
        _update_state_jitted(
            dm.h, dm.hu, dm.hv, dm.source_terms, dm.n,
            fluxes, dt, mesh.edge_to_cell, mesh.cell_areas,
            self.g, self.dry_tolerance
        )

    def step(self, dt: float):
        """
        Performs a single, complete time step of the simulation with a given dt.
        """
        fluxes = self._calculate_fluxes()
        self._update_state(fluxes, dt)
        self.data_manager.update_wse()
