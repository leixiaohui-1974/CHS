import sys
import os
import matplotlib.pyplot as plt

# This is a temporary solution to make the SDK accessible to the example script.
# In a real installation, the SDK would be installed as a package.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'water_system_sdk', 'src')))

from water_system_simulator.simulation_manager import SimulationManager

def run_simple_pid_simulation():
    """
    This function defines the configuration for a simple PID control system
    and runs it using the SimulationManager.
    """
    # This configuration dictionary defines the entire simulation.
    pid_control_config = {
        "simulation_params": {
            "total_time": 100,
            "dt": 0.1
        },
        "components": {
            "reservoir_A": {
                "type": "ReservoirModel",
                "params": {
                    "area": 1.0,
                    "initial_level": 0.0
                }
            },
            "pid_controller": {
                "type": "PIDController",
                "params": {
                    "Kp": 2.0,
                    "Ki": 0.5,
                    "Kd": 1.0,
                    "set_point": 10.0,
                    "output_min": 0.0 # Inflow cannot be negative
                }
            },
            "constant_outflow": {
                "type": "TimeSeriesDisturbance",
                "params": {
                    "times": [0],   # Time point for the constant value
                    "values": [0.5] # Constant outflow of 0.5
                }
            }
        },
        "connections": [
            {
                "source": "reservoir_A.state.level",
                "target": "pid_controller.input.error_source"
            },
            {
                "source": "constant_outflow.output",
                "target": "reservoir_A.input.release_outflow"
            }
        ],
        "execution_order": [
            # 1. PID calculates inflow based on last step's reservoir level
            {
                "component": "pid_controller",
                "method": "step",
                "args": {"dt": "simulation.dt"},
                "result_to": "reservoir_A.input.inflow"
            },
            # 2. Constant outflow is "stepped" (it just provides its value)
            {
                "component": "constant_outflow",
                "method": "step",
                "args": {"dt": "simulation.dt", "t": "simulation.t"}
            },
            # 3. Reservoir level is updated based on new inflow
            {
                "component": "reservoir_A",
                "method": "step",
                "args": {"dt": "simulation.dt"}
            }
        ],
        "logger_config": [
            "reservoir_A.state.level",
            "pid_controller.state.output",
            "reservoir_A.input.inflow"
        ]
    }

    # --- Run the simulation ---
    manager = SimulationManager()
    results_df = manager.run(pid_control_config)

    return results_df

def plot_results(df):
    """Plots the simulation results."""
    plt.figure(figsize=(12, 6))
    plt.plot(df['time'], df['reservoir_A.state.level'], label='Water Level')
    plt.axhline(y=10.0, color='r', linestyle='--', label='Setpoint')
    plt.xlabel('Time (s)')
    plt.ylabel('Water Level (m)')
    plt.title('Simple PID Control Simulation')
    plt.legend()
    plt.grid(True)
    plt.savefig('results/case_01_simple_pid_control.png')
    print("Plot saved to results/case_01_simple_pid_control.png")
    # plt.show()

if __name__ == "__main__":
    # Ensure the results directory exists
    if not os.path.exists('results'):
        os.makedirs('results')

    simulation_results = run_simple_pid_simulation()
    print("Simulation finished. Results:")
    print(simulation_results.head())
    plot_results(simulation_results)
