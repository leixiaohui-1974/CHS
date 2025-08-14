import meshio  # type: ignore
import numpy as np
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

def load_mesh(mesh_file_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Loads an unstructured mesh from a file using meshio.
    Currently supports .msh files with triangular elements.

    Args:
        mesh_file_path (str): Path to the mesh file.

    Returns:
        A tuple containing:
        - points (np.ndarray): Array of node coordinates, shape (num_points, 2).
        - cells (np.ndarray): Array of triangle connectivity, shape (num_cells, 3).
    """
    print(f"Loading mesh from {mesh_file_path}...")
    mesh = meshio.read(mesh_file_path)

    # We only use 2D coordinates, so we discard the z-coordinate if it exists.
    points = mesh.points[:, :2]

    # The model is based on triangular cells. We try to get them and
    # raise an error if they are not present.
    try:
        cells = mesh.get_cells_type('triangle')
    except KeyError:
        raise ValueError("Mesh must contain triangular elements for this model.")

    print(f"Mesh loaded: {points.shape[0]} nodes, {cells.shape[0]} cells.")
    return points, cells


class UnstructuredMesh:
    """
    Manages unstructured mesh data for hydrodynamic simulations on the CPU.

    This class takes raw mesh data (points and cell connectivity), computes
    all necessary geometric properties (e.g., edges, normals, areas), and
    stores them in NumPy arrays.
    """
    def __init__(self, points: np.ndarray, cells: np.ndarray):
        """
        Initializes the mesh, computes geometric properties.

        Args:
            points (np.ndarray): Node coordinates, shape (num_points, 2).
            cells (np.ndarray): Triangle connectivity, shape (num_cells, 3).
        """
        print("Initializing UnstructuredMesh for CPU...")
        self.nodes = np.asarray(points, dtype=np.float64)
        self.cells = np.asarray(cells, dtype=np.int32)

        self.num_nodes = self.nodes.shape[0]
        self.num_cells = self.cells.shape[0]

        print("Computing cell properties...")
        self.cell_centers = self.nodes[self.cells].mean(axis=1)
        self.cell_areas = self._compute_cell_areas()

        print("Computing edge connectivity and properties...")
        (
            self.edges,
            self.edge_to_cell,
            self.cell_to_edge
        ) = self._compute_edge_connectivity()

        self.num_edges = self.edges.shape[0]

        self.edge_normals = self._compute_edge_normals()
        self.edge_lengths = np.linalg.norm(self.edge_normals, axis=1)

        # Normalize the normal vectors to get unit normals
        self.edge_normals /= self.edge_lengths[:, np.newaxis]

        print(f"Mesh initialization complete. Found {self.num_edges} unique edges.")

    def _compute_cell_areas(self) -> np.ndarray:
        """Computes the area of each triangular cell using the Shoelace formula."""
        p1 = self.nodes[self.cells[:, 0]]
        p2 = self.nodes[self.cells[:, 1]]
        p3 = self.nodes[self.cells[:, 2]]

        areas = 0.5 * np.abs(p1[:, 0]*(p2[:, 1] - p3[:, 1]) +
                                p2[:, 0]*(p3[:, 1] - p1[:, 1]) +
                                p3[:, 0]*(p1[:, 1] - p2[:, 1]))
        return np.asarray(areas, dtype=np.float64)

    def _compute_edge_connectivity(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Builds edge connectivity information from the cell connectivity array.
        """
        edges_from_cells = np.vstack([
            self.cells[:, [0, 1]],
            self.cells[:, [1, 2]],
            self.cells[:, [2, 0]]
        ])

        edges_from_cells.sort(axis=1)

        unique_edges, inverse_map = np.unique(edges_from_cells, axis=0, return_inverse=True)

        cell_to_edge = inverse_map.reshape(3, self.num_cells).T

        num_edges = unique_edges.shape[0]
        edge_to_cell = np.full((num_edges, 2), -1, dtype=np.int32)

        for i_cell in range(self.num_cells):
            for i_local_edge in range(3):
                edge_index = cell_to_edge[i_cell, i_local_edge]
                if edge_to_cell[edge_index, 0] == -1:
                    edge_to_cell[edge_index, 0] = i_cell
                else:
                    edge_to_cell[edge_index, 1] = i_cell

        return unique_edges, edge_to_cell, cell_to_edge

    def _compute_edge_normals(self) -> np.ndarray:
        """
        Computes the normal vector for each edge.
        """
        p1 = self.nodes[self.edges[:, 0]]
        p2 = self.nodes[self.edges[:, 1]]

        dx = p2[:, 0] - p1[:, 0]
        dy = p2[:, 1] - p1[:, 1]

        normals = np.hstack([-dy[:, np.newaxis], dx[:, np.newaxis]])

        cell0_idx = self.edge_to_cell[:, 0]
        cell0_centers = self.cell_centers[cell0_idx]

        edge_midpoints = (p1 + p2) / 2
        vec_to_cell0 = cell0_centers - edge_midpoints

        dot_product = np.sum(normals * vec_to_cell0, axis=1)

        mask = dot_product > 1e-9
        normals[mask] *= -1

        return np.asarray(normals, dtype=np.float64)
