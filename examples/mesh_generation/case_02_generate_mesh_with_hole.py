import numpy as np
import sys
import os

# Add the SDK to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'water_system_sdk', 'src')))

from water_system_simulator.meshing.mesh_generator import MeshGenerator

def create_circle_segments(center, radius, num_segments=30):
    """Helper function to create vertices and segments for a circle."""
    angles = np.linspace(0, 2 * np.pi, num_segments, endpoint=False)
    vertices = np.array([[center[0] + radius * np.cos(a), center[1] + radius * np.sin(a)] for a in angles])
    segments = np.array([[i, i + 1] for i in range(num_segments - 1)] + [[num_segments - 1, 0]])
    return vertices, segments

def generate_mesh_with_hole():
    """
    Generates a mesh for a square domain with a circular hole.
    """
    print("Generating a mesh for a square with a circular hole...")

    # 1. Define the outer boundary (a larger square)
    outer_vertices = np.array([
        [-2, -2],
        [2, -2],
        [2, 2],
        [-2, 2],
    ])
    outer_segments = np.array([
        [0, 1], [1, 2], [2, 3], [3, 0]
    ])

    # 2. Define the inner boundary (the circular hole)
    hole_center = (0, 0)
    hole_radius = 0.5
    hole_vertices, hole_segments = create_circle_segments(hole_center, hole_radius)

    # 3. Combine vertices and segments
    # The vertices of the hole are appended to the outer boundary vertices.
    # The segment indices for the hole must be offset by the number of outer vertices.
    all_vertices = np.vstack([outer_vertices, hole_vertices])
    all_segments = np.vstack([outer_segments, hole_segments + len(outer_vertices)])

    # 4. Define a point inside the hole
    # This tells the 'triangle' library to treat the inner boundary as a hole.
    holes = np.array([
        [hole_center[0], hole_center[1]]
    ])

    # 5. Create the PSLG dictionary
    pslg_data = {
        'vertices': all_vertices,
        'segments': all_segments,
        'holes': holes
    }

    # 6. Generate the mesh
    mesh_gen = MeshGenerator()
    mesh_data = mesh_gen.generate(pslg_data, max_area=0.1, quality_meshing=True)

    # 7. Write the mesh to a .msh file
    output_filename = "square_with_hole.msh"
    mesh_gen.write_msh(mesh_data, output_filename)
    print(f"Mesh with hole saved to {output_filename}")
    print("-" * 20)

if __name__ == "__main__":
    # Ensure output directory exists and change into it
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    os.chdir(output_dir)

    generate_mesh_with_hole()
