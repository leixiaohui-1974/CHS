import numpy as np
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve
from .network import HydrodynamicNetwork
from .node import InflowBoundary, LevelBoundary, JunctionNode
from .structures import BaseStructure
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Solver:
    """
    A hydrodynamic solver for unsteady flow in networks of open channels
    based on the St. Venant equations.
    """
    def __init__(self, network: HydrodynamicNetwork, tolerance=1e-4, max_iterations=10, relaxation_factor=0.75, h_min=0.01):
        self.network = network
        self.tolerance = tolerance
        self.max_iterations = max_iterations
        self.relaxation_factor = relaxation_factor
        self.h_min = h_min # Minimum water depth for wet/dry handling
        self.g = 9.81  # gravity

        # Create a unified map for all variables (H, Q, S)
        self.var_map = {}
        node_offset = 0
        reach_offset = len(self.network.nodes)
        struct_offset = reach_offset + len(self.network.reaches)

        for i, node in enumerate(self.network.nodes):
            self.var_map[node.id] = node_offset + i
        for i, reach in enumerate(self.network.reaches):
            self.var_map[reach.id] = reach_offset + i
        for i, struct in enumerate(self.network.structures):
            self.var_map[struct.id] = struct_offset + i

        self.num_nodes = len(self.network.nodes)
        self.num_reaches = len(self.network.reaches)
        self.num_structures = len(self.network.structures)
        self.num_vars = self.num_nodes + self.num_reaches + self.num_structures

    def solve_step(self, dt: float):
        H_old = np.array([node.head for node in self.network.nodes], dtype=float)
        Q_old = np.array([reach.discharge for reach in self.network.reaches], dtype=float)
        S_old = np.array([struct.discharge for struct in self.network.structures], dtype=float)

        H_new = np.copy(H_old)
        Q_new = np.copy(Q_old)
        S_new = np.copy(S_old)

        for k in range(self.max_iterations):
            A = lil_matrix((self.num_vars, self.num_vars))
            B = np.zeros(self.num_vars)

            self._build_matrix(A, B, H_new, Q_new, S_new, H_old, Q_old, S_old, dt)

            try:
                A_csr = A.tocsr()
                if A_csr.nnz == 0:
                    logging.warning("Matrix A is empty. Check network configuration.")
                    return False
                dx = spsolve(A_csr, -B)
            except Exception as e:
                logging.error(f"Could not solve the system: {e}")
                self._revert_to_old_state(H_old, Q_old, S_old)
                return False

            H_new += self.relaxation_factor * dx[0:self.num_nodes]
            Q_new += self.relaxation_factor * dx[self.num_nodes : self.num_nodes + self.num_reaches]
            S_new += self.relaxation_factor * dx[self.num_nodes + self.num_reaches :]

            norm = np.linalg.norm(dx)
            if norm < self.tolerance:
                self._update_network_state(H_new, Q_new, S_new)
                return True

        logging.warning("Solver did not converge within max iterations.")
        self._revert_to_old_state(H_old, Q_old, S_old)
        return False

    def _revert_to_old_state(self, H, Q, S):
        for i, node in enumerate(self.network.nodes): node.head = H[i]
        for i, reach in enumerate(self.network.reaches): reach.discharge = Q[i]
        for i, struct in enumerate(self.network.structures): struct.discharge = S[i]

    def _update_network_state(self, H, Q, S):
        for i, node in enumerate(self.network.nodes): node.head = H[i]
        for i, reach in enumerate(self.network.reaches): reach.discharge = Q[i]
        for i, struct in enumerate(self.network.structures): struct.discharge = S[i]

    def _build_matrix(self, A, B, H_k, Q_k, S_k, H_n, Q_n, S_n, dt):
        # Row index corresponds to the equation for that variable

        # 1. Node Continuity Equations (num_nodes equations)
        for i, node in enumerate(self.network.nodes):
            node_idx = self.var_map[node.id]
            row_idx = node_idx

            # --- Wet/Dry Handling ---
            water_depth = H_k[node_idx] - node.bed_elevation
            if water_depth < self.h_min and not isinstance(node, LevelBoundary):
                # Treat as a dry node. Equation becomes H = bed_elevation.
                A[row_idx, node_idx] = 1.0
                B[row_idx] = H_k[node_idx] - node.bed_elevation
                # Also, set any flows connected to this node to zero.
                # This is handled implicitly by the reach momentum equation's own wet/dry check.
                continue

            # --- Node Storage Term (d(Vol)/dt) ---
            storage_term_coeff = node.surface_area / dt
            A[row_idx, node_idx] = storage_term_coeff
            B[row_idx] = storage_term_coeff * (H_k[node_idx] - H_n[node_idx])

            # --- Flow Terms ---
            inflow_sum = 0
            outflow_sum = 0

            # Reaches flowing in
            for r in self.network.reaches:
                if r.downstream_node.id == node.id:
                    reach_idx_var = self.var_map[r.id]
                    inflow_sum += Q_k[reach_idx_var - self.num_nodes]
                    A[row_idx, reach_idx_var] = -1.0 # dF/dQ_in = -1
            # Structures flowing in
            for s in self.network.structures:
                if s.downstream_node.id == node.id:
                    struct_idx_var = self.var_map[s.id]
                    inflow_sum += S_k[struct_idx_var - self.num_nodes - self.num_reaches]
                    A[row_idx, struct_idx_var] = -1.0 # dF/dQ_in = -1

            # Reaches flowing out
            for r in self.network.reaches:
                if r.upstream_node.id == node.id:
                    reach_idx_var = self.var_map[r.id]
                    outflow_sum += Q_k[reach_idx_var - self.num_nodes]
                    A[row_idx, reach_idx_var] = 1.0 # dF/dQ_out = +1
            # Structures flowing out
            for s in self.network.structures:
                if s.upstream_node.id == node.id:
                    struct_idx_var = self.var_map[s.id]
                    outflow_sum += S_k[struct_idx_var - self.num_nodes - self.num_reaches]
                    A[row_idx, struct_idx_var] = 1.0 # dF/dQ_out = +1

            # Add flow contributions to the B vector. F = ... - (Q_in - Q_out)
            B[row_idx] -= (inflow_sum - outflow_sum)

            # --- Boundary Specific Terms ---
            if isinstance(node, InflowBoundary):
                # F = ... - (Q_in_boundary + Q_in_reaches - Q_out)
                # So we subtract the boundary inflow from B
                B[row_idx] -= node.inflow

            elif isinstance(node, LevelBoundary):
                # Override the continuity equation with a fixed level equation
                # Reset the row first
                A[row_idx, :] = 0
                B[row_idx] = 0
                A[row_idx, node_idx] = 1.0
                B[row_idx] = H_k[node_idx] - node.level

        # 2. Reach Momentum Equations (num_reaches equations)
        for i, reach in enumerate(self.network.reaches):
            reach_idx_var = self.var_map[reach.id]
            row_idx = reach_idx_var

            up_node_idx = self.var_map[reach.upstream_node.id]
            down_node_idx = self.var_map[reach.downstream_node.id]
            reach_idx_Q = reach_idx_var - self.num_nodes

            H_up_k, H_down_k, Q_r_k = H_k[up_node_idx], H_k[down_node_idx], Q_k[reach_idx_Q]
            Q_r_n = Q_n[reach_idx_Q]

            h_up = H_up_k - reach.upstream_node.bed_elevation
            h_down_k = H_down_k - reach.downstream_node.bed_elevation

            # --- Supercritical Flow Handling ---
            froude_up = reach.get_froude_number(h_up, Q_r_k, self.g)
            is_supercritical = froude_up > 1.0

            h_down_eff = h_down_k # Effective h_down to be used in calculations

            if is_supercritical:
                yc = reach.get_critical_depth(Q_r_k, self.g)
                # If downstream is subcritical, it shouldn't influence upstream.
                # Cap the downstream depth at critical depth to enforce this.
                if h_down_k > yc:
                    h_down_eff = yc

            if h_up <= 1e-3 or h_down_eff <= 1e-3:
                A[row_idx, reach_idx_var] = 1.0
                B[row_idx] = Q_r_k
                continue

            A_up = reach.get_area(h_up); A_down = reach.get_area(h_down_eff)
            P_up = reach.get_wetted_perimeter(h_up); P_down = reach.get_wetted_perimeter(h_down_eff)
            Rh_up = A_up / P_up if P_up > 0 else 0; Rh_down = A_down / P_down if P_down > 0 else 0
            A_avg = (A_up + A_down) / 2.0; Rh_avg = (Rh_up + Rh_down) / 2.0
            B_up = reach.get_top_width(h_up); B_down = reach.get_top_width(h_down_eff)
            L = reach.length; n = reach.manning_coefficient

            # Effective downstream water level for pressure term
            H_down_eff = h_down_eff + reach.downstream_node.bed_elevation

            time_term = (Q_r_k - Q_r_n) / dt
            pressure_term = (self.g * A_avg / L) * (H_down_eff - H_up_k)
            conv_term = 0 if L == 0 else ((Q_r_k**2 / A_down if A_down > 0 else 0) - (Q_r_k**2 / A_up if A_up > 0 else 0)) / L

            # Semi-implicit friction term for stability
            S_f = (n**2 * Q_r_k * abs(Q_r_n)) / (A_avg**2 * Rh_avg**(4./3.)) if A_avg > 0 and Rh_avg > 0 else 0
            friction_term = self.g * A_avg * S_f
            B[row_idx] = time_term + conv_term + pressure_term + friction_term

            # --- Jacobian Derivatives ---
            # Derivative of the semi-implicit friction term
            dFric_dQr = (self.g * A_avg * (n**2 * abs(Q_r_n))) / (A_avg**2 * Rh_avg**(4./3.)) if A_avg > 0 and Rh_avg > 0 else 0
            dConv_dQr = 0 if L == 0 else ((2 * Q_r_k / A_down if A_down > 0 else 0) - (2 * Q_r_k / A_up if A_up > 0 else 0)) / L
            A[row_idx, reach_idx_var] = (1.0 / dt) + dConv_dQr + dFric_dQr

            dPress_dHup = (self.g / L) * ( (B_up / 2.0) * (H_down_eff - H_up_k) - A_avg )
            dConv_dHup = 0 if L == 0 else ((Q_r_k**2 * B_up) / (L * A_up**2) if A_up > 0 else 0)
            A[row_idx, up_node_idx] = dConv_dHup + dPress_dHup

            if is_supercritical and h_down_k > yc:
                # If flow is controlled by critical depth, it's independent of H_down.
                A[row_idx, down_node_idx] = 0
            else:
                dPress_dHdown = (self.g / L) * ( (B_down / 2.0) * (H_down_eff - H_up_k) + A_avg )
                dConv_dHdown = 0 if L == 0 else -((Q_r_k**2 * B_down) / (L * A_down**2) if A_down > 0 else 0)
                A[row_idx, down_node_idx] = dConv_dHdown + dPress_dHdown

        # 3. Structure Equations (num_structures equations)
        for i, struct in enumerate(self.network.structures):
            up_node_idx = self.var_map[struct.upstream_node.id]

            H_up = H_k[up_node_idx]
            Q_s = S_k[i] # 'i' is the index in the structures list and S_k array

            # The structure itself adds its equation to the matrix
            struct.add_to_matrix(A, B, self.var_map, H_up, Q_s)
