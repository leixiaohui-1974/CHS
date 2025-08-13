import time
import numpy as np
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'water_system_sdk', 'src')))

from water_system_simulator.hydrodynamics.network import HydrodynamicNetwork
from water_system_simulator.hydrodynamics.node import Node, InflowBoundary, LevelBoundary, JunctionNode
from water_system_simulator.hydrodynamics.reach import Reach
from water_system_simulator.hydrodynamics.solver import Solver as SparseSolver

# --- Define a copy of the old solver that uses numpy.linalg.solve for comparison ---
class DenseSolver(SparseSolver):
    def solve_step(self, dt: float):
        H_old = np.array([node.head for node in self.network.nodes])
        Q_old = np.array([reach.discharge for reach in self.network.reaches])

        H_new = np.copy(H_old)
        Q_new = np.copy(Q_old)

        # Only one iteration is needed for timing comparison
        A = np.zeros((self.num_vars, self.num_vars))
        B = np.zeros(self.num_vars)

        self._build_matrix(A, B, H_new, Q_new, H_old, Q_old, dt)

        try:
            # The key difference: using numpy's dense solver
            dx = np.linalg.solve(A, -B)
        except np.linalg.LinAlgError:
            print("Dense solver failed: Matrix is singular.")
            return False

        H_new += self.relaxation_factor * dx[:self.num_nodes]
        Q_new += self.relaxation_factor * dx[self.num_nodes:]

        # No need for full convergence loop, just timing the solve step
        return True

def build_long_channel_network(num_nodes: int) -> HydrodynamicNetwork:
    """Builds a linear network of nodes and reaches."""
    network = HydrodynamicNetwork()
    nodes = []

    # Create nodes
    inflow_node = InflowBoundary(name="Upstream", inflow=50.0, head=10.0, bed_elevation=5.0)
    nodes.append(inflow_node)

    for i in range(1, num_nodes - 1):
        node = JunctionNode(name=f"Node_{i}", head=9.9 - 0.1*i, bed_elevation=4.9 - 0.1*i)
        nodes.append(node)

    level_node = LevelBoundary(name="Downstream", level=9.9 - 0.1*(num_nodes-1), bed_elevation=4.9 - 0.1*(num_nodes-1))
    nodes.append(level_node)

    # Create reaches connecting the nodes
    for i in range(num_nodes - 1):
        reach = Reach(
            name=f"Reach_{i}",
            upstream_node=nodes[i],
            downstream_node=nodes[i+1],
            length=500,
            manning_coefficient=0.03,
            discharge=50.0
        )
        network.add_reach(reach)

    return network

def run_performance_test():
    """
    Compares the performance of the dense (numpy) and sparse (scipy) solvers.
    """
    num_nodes = 500
    dt = 60  # seconds

    print(f"Building a network with {num_nodes} nodes and {num_nodes - 1} reaches...")
    network = build_long_channel_network(num_nodes)
    print("Network built.")
    print("-" * 30)

    # --- Test Dense Solver (numpy.linalg.solve) ---
    print("Testing Dense Solver...")
    dense_solver = DenseSolver(network)

    start_time_dense = time.time()
    dense_solver.solve_step(dt)
    end_time_dense = time.time()

    duration_dense = end_time_dense - start_time_dense
    print(f"Dense Solver (numpy.linalg.solve) took: {duration_dense:.6f} seconds.")
    print("-" * 30)

    # --- Test Sparse Solver (scipy.sparse.linalg.spsolve) ---
    print("Testing Sparse Solver...")
    sparse_solver = SparseSolver(network)

    start_time_sparse = time.time()
    sparse_solver.solve_step(dt)
    end_time_sparse = time.time()

    duration_sparse = end_time_sparse - start_time_sparse
    print(f"Sparse Solver (scipy.sparse.linalg.spsolve) took: {duration_sparse:.6f} seconds.")
    print("-" * 30)

    # --- Conclusion ---
    if duration_dense > duration_sparse:
        speedup = duration_dense / duration_sparse
        print(f"Conclusion: The sparse solver was {speedup:.2f} times faster than the dense solver.")
    else:
        print("Conclusion: The sparse solver was not faster. This may happen on very small networks.")

if __name__ == "__main__":
    run_performance_test()
