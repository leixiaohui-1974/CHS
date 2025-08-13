import sys
import os
import numpy as np
import matplotlib.pyplot as plt

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from water_system_sdk.src.water_system_simulator.hydrodynamics.node import InflowBoundary, LevelBoundary
from water_system_sdk.src.water_system_simulator.hydrodynamics.reach import Reach
from water_system_sdk.src.water_system_simulator.hydrodynamics.network import HydrodynamicNetwork
from water_system_sdk.src.water_system_simulator.hydrodynamics.solver import Solver

def run_ideal_wave_propagation():
    """
    Sets up and runs a simulation to test wave propagation in an ideal channel.
    """
    # --- 1. Define Simulation Parameters ---
    reach_length = 10000.0  # m
    bottom_width = 50.0  # m
    initial_depth = 10.0  # m
    initial_inflow = 500.0  # m^3/s (gives v=1 m/s)

    dt = 60  # s
    sim_duration = 7200  # s
    time_steps = int(sim_duration / dt)

    # --- 2. Create Network Topology ---
    # We assume bed level is at 0m, so water level (head) = water depth
    inflow_node = InflowBoundary(name="UpstreamInflow", inflow=initial_inflow)
    inflow_node.head = initial_depth # Initial guess for head

    level_node = LevelBoundary(name="DownstreamLevel", level=initial_depth)
    level_node.head = initial_depth # Set initial head for steady state

    reach = Reach(
        name="MainChannel",
        upstream_node=inflow_node,
        downstream_node=level_node,
        length=reach_length,
        manning_coefficient=0.0,  # Ideal: no friction
        bottom_width=bottom_width
    )
    # Set initial discharge
    reach.discharge = initial_inflow

    network = HydrodynamicNetwork()
    network.add_reach(reach)

    # --- 3. Initialize Solver ---
    solver = Solver(network)

    # --- 4. Run Simulation ---
    history_H_up = []
    history_H_down = []
    history_Q = []

    print("Starting simulation...")
    for t in range(time_steps):
        current_time = t * dt

        # Introduce a gradual pulse in the inflow
        pulse_start_time = 500.0
        pulse_end_time = 1500.0
        ramp_duration = 300.0 # 5 minutes to ramp up/down

        if pulse_start_time <= current_time < pulse_start_time + ramp_duration:
            # Ramp up
            factor = (current_time - pulse_start_time) / ramp_duration
            inflow_node.inflow = initial_inflow + 100.0 * factor
        elif pulse_start_time + ramp_duration <= current_time < pulse_end_time - ramp_duration:
            # Hold
            inflow_node.inflow = initial_inflow + 100.0
        elif pulse_end_time - ramp_duration <= current_time < pulse_end_time:
            # Ramp down
            factor = (pulse_end_time - current_time) / ramp_duration
            inflow_node.inflow = initial_inflow + 100.0 * factor
        else:
            inflow_node.inflow = initial_inflow

        # Store current state before the step
        history_H_up.append(network.nodes[solver.node_map[inflow_node.id]].head)
        history_H_down.append(network.nodes[solver.node_map[level_node.id]].head)
        history_Q.append(network.reaches[0].discharge)

        # Solve for the next time step
        if not solver.solve_step(dt):
            print(f"Simulation failed at time {current_time}s")
            break

    print("Simulation finished.")

    # --- 5. Analyze and Plot Results ---
    time_axis = np.arange(0, sim_duration, dt)

    # Theoretical wave speed
    g = 9.81
    c = np.sqrt(g * initial_depth)
    v = initial_inflow / (bottom_width * initial_depth)
    wave_speed = v + c
    theoretical_travel_time = reach_length / wave_speed

    print(f"\n--- Verification ---")
    print(f"Initial flow velocity (v): {v:.2f} m/s")
    print(f"Wave celerity (c = sqrt(g*h)): {c:.2f} m/s")
    print(f"Total wave speed (v+c): {wave_speed:.2f} m/s")
    print(f"Theoretical travel time: {theoretical_travel_time:.0f} s")

    # Find arrival time from simulation
    h_down_array = np.array(history_H_down)
    initial_h_down = h_down_array[0]
    wave_arrival_idx = np.where(h_down_array > initial_h_down + 0.01)[0]

    if len(wave_arrival_idx) > 0:
        wave_arrival_time = time_axis[wave_arrival_idx[0]]
        simulated_travel_time = wave_arrival_time - 500 # Pulse starts at 500s
        print(f"Simulated travel time: {simulated_travel_time:.0f} s")

        error = abs(simulated_travel_time - theoretical_travel_time) / theoretical_travel_time * 100
        print(f"Error: {error:.2f}%")
    else:
        print("Wave did not appear to arrive at the downstream end.")


    # Plotting
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    ax1.plot(time_axis, history_H_up, label='Upstream Head (H_up)')
    ax1.plot(time_axis, history_H_down, label='Downstream Head (H_down)')
    ax1.set_ylabel("Water Level (m)")
    ax1.legend()
    ax1.grid(True)
    ax1.set_title("Ideal Wave Propagation Test")

    ax2.plot(time_axis, history_Q, label='Reach Discharge (Q)')
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Discharge (m^3/s)")
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    plt.savefig("results/case_09_ideal_wave_propagation.png")
    print("\nPlot saved to results/case_09_ideal_wave_propagation.png")
    # plt.show()


if __name__ == "__main__":
    # Ensure the results directory exists
    if not os.path.exists('results'):
        os.makedirs('results')
    run_ideal_wave_propagation()
