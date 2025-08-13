import numpy as np
import sys
import os

# Add the SDK to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'water_system_sdk', 'src')))

from water_system_simulator.meshing.mesh_generator import MeshGenerator

def generate_mesh_with_breakline():
    """
    Generates a mesh for a square domain with a diagonal breakline.
    The breakline must be preserved as edges in the final mesh.
    """
    print("Generating a mesh for a square with a breakline...")

    # Define the vertices of the square, including the endpoints of the breakline
    vertices = np.array([
        [0, 0],  # 0
        [1, 0],  # 1
        [1, 1],  # 2
        [0, 1],  # 3
    ])

    # Define the segments: the four outer edges plus the diagonal breakline
    segments = np.array([
        [0, 1],  # Bottom edge
        [1, 2],  # Right edge
        [2, 3],  # Top edge
        [3, 0],  # Left edge
        [0, 2],  # The diagonal breakline
    ])

    # Create the PSLG dictionary
    pslg_data = {
        'vertices': vertices,
        'segments': segments
    }

    # Generate the mesh
    mesh_gen = MeshGenerator()
    # Using a larger area constraint to make the effect of the breakline more visible
    mesh_data = mesh_gen.generate(pslg_data, max_area=0.1, quality_meshing=True)

    # Write the mesh to a .msh file
    output_filename = "square_with_breakline.msh"
    mesh_gen.write_msh(mesh_data, output_filename)
    print(f"Mesh with breakline saved to {output_filename}")
    print("-" * 20)

if __name__ == "__main__":
    # Ensure output directory exists and change into it
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    os.chdir(output_dir)

    generate_mesh_with_breakline()
