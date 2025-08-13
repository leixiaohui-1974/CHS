import numpy as np
import sys
import os

# Add the SDK to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'water_system_sdk', 'src')))

from water_system_simulator.meshing.mesh_generator import MeshGenerator

def generate_variable_density_mesh():
    """
    Generates a mesh with variable density. The center of the domain will be
    denser than the areas closer to the boundary. This is achieved by defining
    a region with a specific area constraint.
    """
    print("Generating a variable density mesh...")

    # Define the vertices of the square domain
    vertices = np.array([
        [0, 0],
        [2, 0],
        [2, 2],
        [0, 2],
    ])

    # Define the segments for the square's boundary
    segments = np.array([
        [0, 1],
        [1, 2],
        [2, 3],
        [3, 0],
    ])

    # Define regions to control mesh density
    # The format for a region is [x, y, attribute, max_area]
    # We define a region in the center of the domain with a small max_area
    # to make the mesh denser there.
    regions = [
        [1.0, 1.0, 1, 0.01]  # Region at (1,1) with attribute 1 and max area 0.01
    ]

    # Create the PSLG dictionary
    pslg_data = {
        'vertices': vertices,
        'segments': segments,
        'regions': regions
    }

    # Instantiate the mesh generator
    mesh_gen = MeshGenerator()

    # Generate the mesh.
    # The 'a0.1' provides a default max area for the rest of the domain.
    # The region constraint will override this default in the specified area.
    mesh_data = mesh_gen.generate(pslg_data, max_area=0.1, quality_meshing=True)

    # Write the mesh to a .msh file
    output_filename = "square_variable_density.msh"
    mesh_gen.write_msh(mesh_data, output_filename)
    print(f"Variable density mesh saved to {output_filename}")
    print("-" * 20)

if __name__ == "__main__":
    # Ensure output directory exists and change into it
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    os.chdir(output_dir)

    generate_variable_density_mesh()
