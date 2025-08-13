import numpy as np
import sys
import os

# Add the SDK to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'water_system_sdk', 'src')))

from water_system_simulator.meshing.mesh_generator import MeshGenerator

def generate_square_mesh():
    """
    Generates a uniform triangular mesh for a simple square domain.
    """
    print("Generating a uniform mesh for a square...")

    # Define the vertices of the square
    vertices = np.array([
        [0, 0],
        [1, 0],
        [1, 1],
        [0, 1],
    ])

    # Define the segments (the four edges of the square)
    segments = np.array([
        [0, 1],
        [1, 2],
        [2, 3],
        [3, 0],
    ])

    # Create the PSLG dictionary
    pslg_data = {
        'vertices': vertices,
        'segments': segments
    }

    # Instantiate the mesh generator
    mesh_gen = MeshGenerator()

    # Generate the mesh with a maximum triangle area of 0.05
    # The 'q' flag ensures a quality mesh with minimum angle constraints
    mesh_data = mesh_gen.generate(pslg_data, max_area=0.05, quality_meshing=True)

    # Write the mesh to a .msh file
    output_filename = "square_uniform.msh"
    mesh_gen.write_msh(mesh_data, output_filename)
    print(f"Uniform square mesh saved to {output_filename}")
    print("-" * 20)


if __name__ == "__main__":
    # Create an output directory if it doesn't exist
    if not os.path.exists("output"):
        os.makedirs("output")

    # Change to the output directory
    os.chdir("output")

    generate_square_mesh()
