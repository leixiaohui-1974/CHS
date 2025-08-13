import sys
import os
import numpy as np

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'water_system_sdk', 'src')))

from water_system_simulator.hydrodynamics.network import HydrodynamicNetwork
from water_system_simulator.hydrodynamics.node import InflowBoundary, JunctionNode, LevelBoundary
from water_system_simulator.hydrodynamics.structures import WeirStructure
from water_system_simulator.hydrodynamics.solver import Solver

def build_weir_test_network():
    """
    Builds a simple network with a weir structure.
    Topology: (Inflow) -> Node1 -> Weir -> Node2 -> (Outflow)
    """
    network = HydrodynamicNetwork()

    # Define Nodes
    # Water comes in at 10 m3/s. Initial water level is below weir crest.
    node_inflow = InflowBoundary(name="Inflow", inflow=10.0, head=10.5, bed_elevation=5.0)

    # Node upstream of the weir
    node_up = JunctionNode(name="UpstreamOfWeir", head=10.5, bed_elevation=5.0)

    # Node downstream of the weir
    node_down = JunctionNode(name="DownstreamOfWeir", head=8.0, bed_elevation=4.5)

    # Outflow boundary
    node_outflow = LevelBoundary(name="Outflow", level=8.0, bed_elevation=4.5)

    # Define Weir Structure
    # Weir crest is at 11.0m. Water must rise to flow over it.
    weir = WeirStructure(
        name="MainWeir",
        upstream_node=node_up,
        downstream_node=node_down,
        crest_elevation=11.0,
        weir_coefficient=1.7,
        crest_width=15.0,
        discharge=0.0 # Initially no flow
    )

    # This setup is a bit artificial. In a real model, we would have reaches.
    # To make the system solvable, we need to connect the boundary nodes to the weir nodes.
    # A common way is to use very short, non-resistant reaches.
    # However, for this test, we can try to directly connect the Inflow to the weir's upstream node
    # and the weir's downstream node to the outflow.
    # The solver's continuity equation at the JunctionNode should handle this.

    # Let's adjust the topology to be more direct for a simple test:
    # (Inflow) -> Weir -> (Outflow)

    network_simple = HydrodynamicNetwork()
    node_inflow_direct = InflowBoundary(name="Inflow", inflow=10.0, head=10.5, bed_elevation=5.0, surface_area=5000)
    # The head of a level boundary should be initialized to its fixed level
    node_outflow_direct = LevelBoundary(name="Outflow", level=8.0, head=8.0, bed_elevation=4.5, surface_area=5000)

    weir_direct = WeirStructure(
        name="MainWeir",
        upstream_node=node_inflow_direct,
        downstream_node=node_outflow_direct,
        crest_elevation=11.0,
        weir_coefficient=1.7,
        crest_width=15.0,
        discharge=0.0
    )

    # The continuity at InflowBoundary is now Q_struct = inflow
    # The equation for LevelBoundary is H_down = level
    # The equation for the Weir is Q_struct = f(H_up)
    # The unknowns are H_up, H_down, Q_struct. We have 3 equations, 3 unknowns.
    # But H_up is the head at the InflowBoundary, which is also an unknown.
    # H_down is the head at the LevelBoundary, which is fixed.
    # So unknowns are H_inflow, Q_weir. Equations are Q_weir=inflow, Q_weir=f(H_inflow).
    # This should solve for H_inflow.

    network_simple.add_structure(weir_direct)

    return network_simple

def run_weir_simulation():
    """
    Runs a simulation of water flowing over a weir.
    """
    print("Building weir network...")
    network = build_weir_test_network()

    # The solver expects at least one reach for now due to indexing.
    # This is a flaw in the solver design. Let's add a dummy reach.
    # This highlights a need for further refactoring, but we can work around it for now.
    from water_system_simulator.hydrodynamics.reach import Reach
    dummy_reach = Reach("dummy", network.nodes[0], network.nodes[1], length=1, manning_coefficient=0.0)
    # network.add_reach(dummy_reach) # Let's try without it first. The refactoring should have fixed this.

    print(f"Network: {network}")
    print("Initial state:")
    print(f"  Upstream Node '{network.structures[0].upstream_node.name}': Head = {network.structures[0].upstream_node.head:.2f} m")
    print(f"  Downstream Node '{network.structures[0].downstream_node.name}': Head = {network.structures[0].downstream_node.head:.2f} m")
    print(f"  Weir '{network.structures[0].name}': Discharge = {network.structures[0].discharge:.2f} m3/s, Crest = {network.structures[0].crest_elevation:.2f} m")
    print("-" * 30)

    solver = Solver(network, max_iterations=20, relaxation_factor=0.5)
    dt = 2  # seconds
    num_steps = 800 # Increase steps to reach steady state

    print(f"Running simulation for {num_steps} steps with dt={dt}s...")

    for step in range(num_steps):
        success = solver.solve_step(dt)
        if not success:
            print(f"Solver failed at step {step + 1}. Halting simulation.")
            break

        if (step + 1) % 20 == 0:
            print(f"  Step {step+1:3d}: "
                  f"Upstream Head={network.structures[0].upstream_node.head:.3f} m, "
                  f"Weir Flow={network.structures[0].discharge:.3f} m3/s")

    print("-" * 30)
    print("Final state:")
    final_head = network.structures[0].upstream_node.head
    final_flow = network.structures[0].discharge
    crest = network.structures[0].crest_elevation

    print(f"  Upstream Node '{network.structures[0].upstream_node.name}': Head = {final_head:.3f} m")
    print(f"  Weir '{network.structures[0].name}': Discharge = {final_flow:.3f} m3/s")

    # --- Verification ---
    print("\n--- Verification ---")
    if final_flow > 9.9 and final_flow < 10.1:
        print(f"PASSED: Final weir discharge ({final_flow:.2f}) is approximately equal to inflow (10.0).")
    else:
        print(f"FAILED: Final weir discharge ({final_flow:.2f}) is not close to inflow (10.0).")

    # Check if upstream water level is correctly calculated
    # Q = C * b * (H_up - Z_crest)^(3/2)  =>  H_up = Z_crest + (Q / (C*b))^(2/3)
    weir = network.structures[0]
    expected_head = weir.crest_elevation + (weir.discharge / (weir.weir_coefficient * weir.crest_width)) ** (2/3)

    print(f"Theoretical upstream head for this flow: {expected_head:.3f} m")
    if abs(final_head - expected_head) < 0.01:
        print(f"PASSED: Final upstream head ({final_head:.3f}) is close to theoretical value.")
    else:
        print(f"FAILED: Final upstream head ({final_head:.3f}) is not close to theoretical value.")


if __name__ == "__main__":
    run_weir_simulation()
