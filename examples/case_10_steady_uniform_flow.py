import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from water_system_sdk.src.water_system_simulator.hydrodynamics.node import InflowBoundary, LevelBoundary
from water_system_sdk.src.water_system_simulator.hydrodynamics.reach import Reach
from water_system_sdk.src.water_system_simulator.hydrodynamics.network import HydrodynamicNetwork
from water_system_sdk.src.water_system_simulator.hydrodynamics.solver import Solver

def manning_equation(y, Q, n, S0, b, z):
    """Manning's equation for a trapezoidal channel, rearranged for root finding."""
    A = (b + z * y) * y
    P = b + 2 * y * np.sqrt(1 + z**2)
    if A <= 0 or P <= 0:
        return Q # Return a large residual if depth is non-positive
    Rh = A / P
    # Q_calc = (1/n) * A * Rh**(2/3) * np.sqrt(S0)
    # The equation below avoids potential issues with sqrt(negative S0) if S0 is ever negative
    Q_calc = (A * Rh**(2/3) * np.sign(S0) * np.sqrt(abs(S0))) / n
    return Q - Q_calc

def calculate_normal_depth(Q, n, S0, b, z):
    """Calculates normal depth (y_n) by solving Manning's equation."""
    # Use fsolve to find the root of the Manning equation
    y_initial_guess = (Q * n / (b * np.sqrt(S0)))**0.6 if S0 > 0 else 1.0
    y_n, = fsolve(manning_equation, y_initial_guess, args=(Q, n, S0, b, z))
    return y_n

def run_steady_uniform_flow_test():
    """
    Sets up and runs a simulation to test steady, uniform flow in a prismatic channel.
    """
    # --- 1. Define Channel and Flow Parameters ---
    Q_inflow = 100.0  # m^3/s
    slope = 1e-3  # 0.001 m/m
    manning_n = 0.03
    bottom_width = 20.0 # m
    side_slope = 1.5 # 1.5H:1V

    dt = 60  # s
    sim_duration = 10000  # s, run long enough to ensure steady state
    time_steps = int(sim_duration / dt)

    # --- 2. Calculate Expected Normal Depth ---
    y_n = calculate_normal_depth(Q_inflow, manning_n, slope, bottom_width, side_slope)
    print(f"--- Theoretical Calculation ---")
    print(f"Calculated Normal Depth (y_n): {y_n:.3f} m")

    # --- 3. Create Network Topology ---
    # Assume downstream bed elevation is 0, so downstream head = y_n
    # Upstream bed elevation will be higher due to slope
    reach_length = 5000.0 # m
    z_down = 0.0
    z_up = z_down + slope * reach_length

    # The LevelBoundary level is a water surface elevation (head)
    downstream_level = z_down + y_n

    inflow_node = InflowBoundary(name="UpstreamInflow", inflow=Q_inflow, bed_elevation=z_up)
    level_node = LevelBoundary(name="DownstreamLevel", level=downstream_level, bed_elevation=z_down)

    reach = Reach(
        name="MainChannel",
        upstream_node=inflow_node,
        downstream_node=level_node,
        length=reach_length,
        manning_coefficient=manning_n,
        bed_slope=slope,
        bottom_width=bottom_width,
        side_slope=side_slope
    )

    # Initial conditions: start close to the expected steady state
    inflow_node.head = z_up + y_n
    level_node.head = downstream_level
    reach.discharge = Q_inflow

    network = HydrodynamicNetwork()
    network.add_reach(reach)

    # --- 4. Initialize and Run Solver ---
    solver = Solver(network)

    print("\n--- Simulation ---")
    print(f"Running simulation for {sim_duration}s...")
    for t in range(time_steps):
        if not solver.solve_step(dt):
            print(f"Simulation failed at time {t*dt}s")
            break
    print("Simulation finished.")

    # --- 5. Analyze and Verify Results ---
    final_H_up = inflow_node.head
    final_H_down = level_node.head
    final_Q = reach.discharge

    final_y_up = final_H_up - z_up
    final_y_down = final_H_down - z_down

    print("\n--- Verification ---")
    print(f"Expected depth: {y_n:.3f} m")
    print(f"Simulated upstream depth: {final_y_up:.3f} m")
    print(f"Simulated downstream depth: {final_y_down:.3f} m")
    print("-" * 20)
    print(f"Expected discharge: {Q_inflow:.2f} m^3/s")
    print(f"Simulated discharge: {final_Q:.2f} m^3/s")

    # Check if results are close to theoretical values
    depth_error = abs(final_y_up - y_n) / y_n
    discharge_error = abs(final_Q - Q_inflow) / Q_inflow

    print("\n--- Errors ---")
    print(f"Depth error: {depth_error:.2%}")
    print(f"Discharge error: {discharge_error:.2%}")

    if depth_error < 0.01 and discharge_error < 0.01:
        print("\nSUCCESS: Simulation results match theoretical steady, uniform flow.")
    else:
        print("\nFAILURE: Simulation results do not match theoretical values.")

if __name__ == "__main__":
    run_steady_uniform_flow_test()
