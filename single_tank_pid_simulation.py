# -*- coding: utf-8 -*-
"""
A standalone simulation script for PID control of a single water tank.

This script uses the foundational modules from the water_system_simulator library
to simulate controlling the water level in a single tank to a desired setpoint.

The simulation parameters are designed to be easily configurable in the
"SIMULATION CONFIGURATION" section below.

The script will save the full simulation results to a CSV file.
"""
import sys
import os

# Add the package to the Python path to ensure modules can be imported
# This assumes the script is run from the root of the repository
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from water_system_simulator.basic_tools.loggers import CSVLogger
from water_system_simulator.modeling.storage_models import FirstOrderInertiaModel
from water_system_simulator.control.pid_controller import PIDController

# --- SIMULATION CONFIGURATION ---

# Simulation Time Parameters
SIMULATION_TIME = 300  # Total simulation time in seconds
DT = 1.0               # Time step in seconds

# Tank Model Parameters
# This represents a simple tank where outflow is proportional to storage level.
# The time_constant can be seen as the tank's resistance to level changes.
TANK_INITIAL_STORAGE = 0.0  # Initial water level/storage in the tank (e.g., meters)
TANK_TIME_CONSTANT = 20.0   # A higher value means the tank drains slower

# PID Controller Parameters
KP = 2.5  # Proportional gain
KI = 0.1  # Integral gain
KD = 1.0  # Derivative gain
SETPOINT = 10.0  # Target water level/storage for the tank (e.g., meters)

# Output File
OUTPUT_CSV_FILE = "single_tank_simulation_log.csv"

# --- SIMULATION SCRIPT ---

def run_single_tank_simulation():
    """
    Runs the single-tank PID control simulation.
    """
    print("Starting single-tank PID simulation...")

    # Calculate number of simulation steps
    n_steps = int(SIMULATION_TIME / DT)

    # 1. Initialize the system components
    # Initialize the tank model using the configuration
    tank = FirstOrderInertiaModel(
        initial_storage=TANK_INITIAL_STORAGE,
        time_constant=TANK_TIME_CONSTANT
    )

    # Initialize the PID controller using the configuration
    pid_controller = PIDController(
        kp=KP,
        ki=KI,
        kd=KD,
        setpoint=SETPOINT
    )

    # Initialize the CSV logger to save the results
    logger = CSVLogger(
        filename=OUTPUT_CSV_FILE,
        headers=["time", "water_level", "control_output", "setpoint"]
    )

    print(f"Simulation will run for {SIMULATION_TIME} seconds with a time step of {DT}s.")
    print(f"Results will be saved to '{OUTPUT_CSV_FILE}'.")

    # 2. Run the simulation loop
    for i in range(n_steps):
        current_time = i * DT

        # Get the current water level from the tank model
        current_level = tank.storage

        # Calculate the required inflow using the PID controller
        # The controller's output is the command for the inflow valve/pump
        inflow_command = pid_controller.calculate(current_level, DT)

        # In a real system, the inflow might be limited (e.g., a valve can't be negative)
        # We'll ensure the inflow is not negative.
        inflow = max(0, inflow_command)

        # Update the tank's state by providing the net inflow.
        # In this simple model, the calculated inflow is the net inflow.
        tank.step(inflow)

        # Log the current state to the CSV file
        logger.log([current_time, current_level, inflow, SETPOINT])

    print("Simulation complete.")
    print(f"Final water level: {tank.storage:.2f}")

# Main execution block
if __name__ == "__main__":
    run_single_tank_simulation()
