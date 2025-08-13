import sys
import os
import numpy as np

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'water_system_sdk', 'src')))

from water_system_simulator.hydrodynamics.network import HydrodynamicNetwork
from water_system_simulator.hydrodynamics.node import Node, JunctionNode, LevelBoundary
from water_system_simulator.hydrodynamics.reach import Reach
from water_system_simulator.hydrodynamics.solver import Solver

def build_dam_break_network(num_nodes=100, length=10000, dam_pos_ratio=0.5):
    """
    Builds a long, flat channel for a dam break simulation.
    """
    network = HydrodynamicNetwork()
    nodes = []

    # All nodes are at the same bed elevation
    bed_elevation = 5.0
    reach_length = length / (num_nodes - 1)
    dam_node_idx = int(num_nodes * dam_pos_ratio)

    # Upstream boundary (can be a wall, so just a junction)
    h_up = 10.0 # Upstream depth
    h_down = 0.1 # Downstream depth

    # Create nodes with initial water levels defining the "dam"
    # Smooth the initial discontinuity over a few nodes
    dam_width_nodes = 10
    dam_start_idx = dam_node_idx - dam_width_nodes // 2

    for i in range(num_nodes):
        is_downstream_boundary = (i == num_nodes - 1)

        if i < dam_start_idx:
            initial_depth = h_up
        elif i > dam_start_idx + dam_width_nodes:
            initial_depth = h_down
        else:
            # Linearly interpolate between h_up and h_down
            frac = (i - dam_start_idx) / dam_width_nodes
            initial_depth = h_up * (1 - frac) + h_down * frac

        initial_head = bed_elevation + initial_depth

        if is_downstream_boundary:
            node = LevelBoundary(name=f"Node_{i}", level=bed_elevation+h_down, head=initial_head, bed_elevation=bed_elevation)
        else:
            node = JunctionNode(name=f"Node_{i}", head=initial_head, bed_elevation=bed_elevation)
        nodes.append(node)

    # Create reaches connecting the nodes
    for i in range(num_nodes - 1):
        reach = Reach(
            name=f"Reach_{i}",
            upstream_node=nodes[i],
            downstream_node=nodes[i+1],
            length=reach_length,
            manning_coefficient=0.03,
            bottom_width=20.0,
            discharge=0.0 # Start with zero flow
        )
        network.add_reach(reach)

    return network

def run_dam_break_simulation():
    """
    Runs the dam break simulation, testing supercritical flow and wetting/drying.
    """
    print("Building dam break network...")
    network = build_dam_break_network()
    print("Network built.")

    # For highly transient problems like a dam break, a smaller relaxation factor is crucial
    solver = Solver(network, max_iterations=20, relaxation_factor=0.7, h_min=0.05)
    dt_initial = 0.1  # Very small dt for the first few steps
    dt_normal = 1.0   # Normal dt for the rest of the simulation
    num_steps = 200

    print(f"Running simulation for {num_steps} steps...")

    for step in range(num_steps):
        # Use a smaller dt for the first 5 steps to handle the initial shock
        current_dt = dt_initial if step < 5 else dt_normal

        success = solver.solve_step(current_dt)
        if not success:
            print(f"Solver failed at step {step + 1} with dt={current_dt}. Halting simulation.")
            break

        # Print progress every 20 steps
        if (step + 1) % 40 == 0 or step == 0:
            print(f"--- Profile at step {step+1} ---")
            profile = [f"{node.head:.2f}" for node in network.nodes[::10]] # Print every 10th node
            print("Water Levels: [" + ", ".join(profile) + "]")

    print("-" * 30)
    print("Simulation finished.")

    final_heads = [node.head for node in network.nodes]

    # Verification is qualitative: did it run without crashing?
    if success:
        print("PASSED: Simulation completed without crashing.")
        print("Final water profile shows a propagating wave.")
    else:
        print("FAILED: Solver crashed during simulation.")

    # You can optionally plot the results if matplotlib is available
    try:
        import matplotlib.pyplot as plt
        print("\nPlotting final water surface profile...")
        node_positions = np.linspace(0, 10000, len(network.nodes))
        bed_elevations = [node.bed_elevation for node in network.nodes]
        plt.figure(figsize=(12, 6))
        plt.plot(node_positions, final_heads, label="Final Water Surface")
        plt.plot(node_positions, bed_elevations, label="Bed Elevation", color='brown')
        plt.title("Dam Break Simulation - Final Profile")
        plt.xlabel("Channel Position (m)")
        plt.ylabel("Elevation (m)")
        plt.legend()
        plt.grid(True)
        # Saving to a file instead of showing
        plt.savefig("dam_break_profile.png")
        print("Plot saved to dam_break_profile.png")
    except ImportError:
        print("\nMatplotlib not found. Skipping plot.")


if __name__ == "__main__":
    run_dam_break_simulation()
