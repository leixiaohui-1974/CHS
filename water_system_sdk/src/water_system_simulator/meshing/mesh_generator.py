import numpy as np
import triangle as tr  # type: ignore

class MeshGenerator:
    """
    A class to generate 2D unstructured triangular meshes using the 'triangle' library.

    This class provides methods to generate meshes from Planar Straight Line Graphs (PSLGs)
    and write them to Gmsh .msh files.

    The input PSLG is a dictionary with the following keys:
    - 'vertices': A NumPy array of shape (N, 2) defining the vertex coordinates.
    - 'segments': A NumPy array of shape (M, 2) defining the segments using vertex indices.
    - 'holes': A NumPy array of shape (K, 2) with coordinates of points inside holes.
    - 'regions': A list of lists, where each inner list contains [x, y, attribute, max_area].
                This is used for defining regions with specific attributes and mesh size constraints.
    """

    def __init__(self):
        pass

    def generate(self, pslg_data, max_area=None, quality_meshing=True):
        """
        Generates a triangular mesh for a given Planar Straight Line Graph (PSLG).

        Args:
            pslg_data (dict): The input PSLG data dictionary.
            max_area (float, optional): The maximum area constraint for triangles.
                                        If specified, it triggers area-controlled meshing.
            quality_meshing (bool, optional): If True, enables quality meshing with a minimum
                                              angle constraint (default is 20 degrees).

        Returns:
            dict: A dictionary containing the generated mesh data from triangle.triangulate.
        """
        opts = 'p' # 'p' for PSLG
        if quality_meshing:
            opts += 'q' # 'q' for quality meshing (min angle 20 degrees)

        if max_area:
            opts += f'a{max_area}'

        # The triangle library requires at least 'vertices' or 'segments'.
        if 'vertices' not in pslg_data and 'segments' not in pslg_data:
            raise ValueError("pslg_data must contain at least 'vertices' or 'segments'.")

        mesh = tr.triangulate(pslg_data, opts=opts)
        return mesh

    def write_msh(self, mesh_data, filename):
        """
        Writes the mesh data to a file in Gmsh MSH version 2 ASCII format.

        Args:
            mesh_data (dict): A dictionary containing the mesh data, typically the
                              output from the triangle.triangulate function.
                              It must contain 'vertices' and 'triangles' keys.
            filename (str): The path to the output .msh file.
        """
        if 'vertices' not in mesh_data or 'triangles' not in mesh_data:
            raise ValueError("mesh_data must contain 'vertices' and 'triangles' keys.")

        vertices = mesh_data['vertices']
        triangles = mesh_data['triangles']

        with open(filename, 'w') as f:
            # Header
            f.write("$MeshFormat\n")
            f.write("2.2 0 8\n")
            f.write("$EndMeshFormat\n")

            # Nodes
            f.write("$Nodes\n")
            f.write(f"{len(vertices)}\n")
            for i, v in enumerate(vertices):
                f.write(f"{i + 1} {v[0]} {v[1]} 0.0\n")
            f.write("$EndNodes\n")

            # Elements
            f.write("$Elements\n")
            f.write(f"{len(triangles)}\n")
            # Element type for a 3-node triangle is 2.
            # We'll use 2 tags: physical entity and geometrical entity (defaults).
            num_tags = 2
            physical_entity = 1  # Default physical group
            geometrical_entity = 1 # Default geometrical entity

            for i, t in enumerate(triangles):
                # Gmsh elements are 1-based
                f.write(f"{i + 1} 2 {num_tags} {physical_entity} {geometrical_entity} {t[0] + 1} {t[1] + 1} {t[2] + 1}\n")
            f.write("$EndElements\n")

        print(f"Mesh successfully written to {filename}")
