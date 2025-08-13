import yaml
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
import meshio

# Adjust path to import from the SDK
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from water_system_sdk.src.water_system_simulator.simulation_manager import SimulationManager

def setup_test_mesh():
    """Creates the simple mesh file needed for the test."""
    mesh_file = "test_slope.msh"
    if os.path.exists(mesh_file):
        return mesh_file # Avoid recreating if it exists

    points = np.array([
        [0.0, 0.0, 0.0], [10.0, 0.0, 0.0],
        [0.0, 10.0, 0.0], [10.0, 10.0, 0.0]
    ])
    cells = [("triangle", np.array([[0, 1, 2], [1, 3, 2]]))]
    mesh = meshio.Mesh(points, cells)
    meshio.write(mesh_file, mesh)
    return mesh_file

def cleanup_test_mesh(mesh_file):
    """Removes the created mesh file."""
    if os.path.exists(mesh_file):
        os.remove(mesh_file)

def run_inflow_simulation():
    """
    Runs the 2D inflow simulation and returns the results.
    """
    config_path = os.path.join(os.path.dirname(__file__), "12_simple_2d_inflow.yml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    manager = SimulationManager()
    results_df = manager.run(config)
    return results_df

def plot_results(df):
    """Plots the total volume over time."""
    # The output of the floodplain model is a dictionary. We need to extract the volume.
    volumes = [d['total_volume_m3'] for d in df['floodplain.output'] if d]
    times = df.loc[df['floodplain.output'].notna(), 'time']

    plt.figure(figsize=(10, 6))
    plt.plot(times, volumes, 'b-', label='Total Water Volume')
    plt.xlabel("Time (s)")
    plt.ylabel("Volume (m^3)")
    plt.title("2D Floodplain Inflow Test")
    plt.legend()
    plt.grid(True)

    plot_dir = "results"
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)
    plot_path = os.path.join(plot_dir, "case_12_2d_inflow.png")
    plt.savefig(plot_path)
    print(f"\nPlot saved to {plot_path}")

def main():
    """Main execution function."""
    mesh_file = None
    try:
        mesh_file = setup_test_mesh()
        results = run_inflow_simulation()

        print("Simulation Results (last 5 steps):")
        print(results.tail())

        # Verification
        # Extract the volume data, ignoring potential None values if logging happens on different steps
        volumes = [d['total_volume_m3'] for d in results['floodplain.output'] if d is not None]
        initial_volume = volumes[0]
        final_volume = volumes[-1]

        print(f"\nInitial Volume: {initial_volume:.4f} m^3")
        print(f"Final Volume:   {final_volume:.4f} m^3")

        assert final_volume > initial_volume, "Final volume should be greater than initial volume."

        # The expected final volume is inflow_rate * total_time = 0.1 * 100 = 10
        # Check if it's reasonably close.
        expected_volume = 10.0
        assert abs(final_volume - expected_volume) < 0.1, \
            f"Final volume {final_volume:.4f} is not close to the expected {expected_volume:.4f}."

        print("\nIntegration test passed successfully!")

        plot_results(results)

    finally:
        if mesh_file:
            cleanup_test_mesh(mesh_file)

if __name__ == "__main__":
    main()
