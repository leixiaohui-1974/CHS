import numpy as np
from .network import HydrodynamicNetwork
from .node import InflowBoundary, LevelBoundary, JunctionNode
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Solver:
    """
    A hydrodynamic solver for unsteady flow in networks of open channels
    based on the St. Venant equations.
    """
    def __init__(self, network: HydrodynamicNetwork, tolerance=1e-4, max_iterations=10):
        self.network = network
        self.tolerance = tolerance
        self.max_iterations = max_iterations
        self.g = 9.81  # gravity

        self.node_map = {node.id: i for i, node in enumerate(self.network.nodes)}
        self.reach_map = {reach.id: i for i, reach in enumerate(self.network.reaches)}

        self.num_nodes = len(self.network.nodes)
        self.num_reaches = len(self.network.reaches)
        self.num_vars = self.num_nodes + self.num_reaches

    def solve_step(self, dt: float):
        H_old = np.array([node.head for node in self.network.nodes])
        Q_old = np.array([reach.discharge for reach in self.network.reaches])

        H_new = np.copy(H_old)
        Q_new = np.copy(Q_old)

        for k in range(self.max_iterations):
            A = np.zeros((self.num_vars, self.num_vars))
            B = np.zeros(self.num_vars)

            self._build_matrix(A, B, H_new, Q_new, H_old, Q_old, dt)

            try:
                dx = np.linalg.solve(A, -B)
            except np.linalg.LinAlgError:
                logging.error("Matrix is singular. Could not solve the system.")
                for i, node in enumerate(self.network.nodes): node.head = H_old[i]
                for i, reach in enumerate(self.network.reaches): reach.discharge = Q_old[i]
                return False

            H_new += dx[:self.num_nodes]
            Q_new += dx[self.num_nodes:]

            norm = np.linalg.norm(dx)
            if norm < self.tolerance:
                for i, node in enumerate(self.network.nodes): node.head = H_new[i]
                for i, reach in enumerate(self.network.reaches): reach.discharge = Q_new[i]
                return True

        logging.warning("Solver did not converge within max iterations.")
        for i, node in enumerate(self.network.nodes): node.head = H_old[i]
        for i, reach in enumerate(self.network.reaches): reach.discharge = Q_old[i]
        return False

    def _build_matrix(self, A, B, H_k, Q_k, H_n, Q_n, dt):
        row_idx = 0

        # 1. Node Continuity Equations
        for i, node in enumerate(self.network.nodes):
            node_idx = self.node_map[node.id]
            if isinstance(node, InflowBoundary):
                reach_idx = self.reach_map[self.network.reaches[0].id]
                A[row_idx, self.num_nodes + reach_idx] = 1.0
                B[row_idx] = Q_k[reach_idx] - node.inflow
            elif isinstance(node, LevelBoundary):
                A[row_idx, node_idx] = 1.0
                B[row_idx] = H_k[node_idx] - node.level
            row_idx += 1

        # 2. Reach Momentum Equations
        for i, reach in enumerate(self.network.reaches):
            reach_idx = self.reach_map[reach.id]
            up_node = reach.upstream_node
            down_node = reach.downstream_node
            up_node_idx = self.node_map[up_node.id]
            down_node_idx = self.node_map[down_node.id]

            H_up_k, H_down_k, Q_r_k = H_k[up_node_idx], H_k[down_node_idx], Q_k[reach_idx]
            Q_r_n = Q_n[reach_idx]

            z_up = up_node.bed_elevation
            z_down = down_node.bed_elevation
            h_up = H_up_k - z_up
            h_down = H_down_k - z_down

            if h_up <= 1e-3 or h_down <= 1e-3:
                A[row_idx, self.num_nodes + reach_idx] = 1.0; B[row_idx] = Q_r_k
                row_idx += 1
                continue

            A_up = reach.get_area(h_up); A_down = reach.get_area(h_down)
            P_up = reach.get_wetted_perimeter(h_up); P_down = reach.get_wetted_perimeter(h_down)
            Rh_up = A_up / P_up; Rh_down = A_down / P_down
            A_avg = (A_up + A_down) / 2.0; Rh_avg = (Rh_up + Rh_down) / 2.0

            B_up = reach.get_top_width(h_up); B_down = reach.get_top_width(h_down)
            L = reach.length; n = reach.manning_coefficient

            # --- Momentum Equation F(...) = 0 ---
            # F = time + convective + pressure + friction

            time_term = (Q_r_k - Q_r_n) / dt
            pressure_term = (self.g * A_avg / L) * (H_down_k - H_up_k)
            conv_term = ((Q_r_k**2 / A_down) - (Q_r_k**2 / A_up)) / L

            S_f = (n**2 * Q_r_k * abs(Q_r_k)) / (A_avg**2 * Rh_avg**(4./3.)) if A_avg > 0 and Rh_avg > 0 else 0
            friction_term = self.g * A_avg * S_f

            B[row_idx] = time_term + conv_term + pressure_term + friction_term

            # --- Jacobian coefficients (derivatives of F) ---
            dFric_dQr = (self.g * A_avg * (n**2 * 2 * abs(Q_r_k))) / (A_avg**2 * Rh_avg**(4./3.)) if A_avg > 0 and Rh_avg > 0 else 0
            dConv_dQr = ((2 * Q_r_k / A_down) - (2 * Q_r_k / A_up)) / L
            A[row_idx, self.num_nodes + reach_idx] = (1.0 / dt) + dConv_dQr + dFric_dQr

            dPress_dHup = (self.g / L) * ( (B_up / 2.0) * (H_down_k - H_up_k) - A_avg )
            dConv_dHup = ((Q_r_k**2 * B_up) / (L * A_up**2))
            A[row_idx, up_node_idx] = dConv_dHup + dPress_dHup

            dPress_dHdown = (self.g / L) * ( (B_down / 2.0) * (H_down_k - H_up_k) + A_avg )
            dConv_dHdown = -((Q_r_k**2 * B_down) / (L * A_down**2))
            A[row_idx, down_node_idx] = dConv_dHdown + dPress_dHdown

            row_idx += 1
