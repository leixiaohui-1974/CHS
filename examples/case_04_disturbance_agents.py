import sys
import os
import pandas as pd
import matplotlib.pyplot as plt

# Add the root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from water_system_sdk.src.water_system_simulator.simulation_manager import SimulationManager

def run_disturbance_agent_simulation():
    """
    This example demonstrates the use of the new disturbance agents:
    - RainfallAgent: Simulates inflow into a reservoir.
    - DemandAgent: Simulates water demand from the reservoir.
    - FaultAgent: Simulates a sensor drift on the water level measurement.
    """
    config = {
        "simulation_params": {
            "total_time": 200,
            "dt": 1.0
        },
        "components": {
            "inflow_agent": {
                "type": "RainfallAgent",
                "params": {
                    "rainfall_pattern": [5.0] * 50 + [2.0] * 50 + [8.0] * 100
                }
            },
            "demand_agent": {
                "type": "DemandAgent",
                "params": {
                    "demand_pattern": [3.0] * 100 + [4.0] * 100
                }
            },
            "level_sensor_fault": {
                "type": "FaultAgent",
                "params": {
                    "fault_sequence": [
                        {
                            "type": "SensorDrift",
                            "start_time": 100,
                            "drift_rate": 0.05 # m per second
                        }
                    ]
                }
            },
            "reservoir": {
                "type": "ReservoirModel",
                "params": {
                    "initial_level": 5.0,
                    "area": 100,
                    "max_level": 10.0
                }
            },
            "pid_controller": {
                "type": "PIDController",
                "params": {
                    "Kp": 0.5,
                    "Ki": 0.1,
                    "Kd": 0.01,
                    "set_point": 5.0 # Target water level
                }
            }
        },
        "connections": [
            # Rainfall provides inflow to the reservoir
            {"source": "inflow_agent.output", "target": "reservoir.input.inflow"},
            # Demand is an outflow from the reservoir
            {"source": "demand_agent.output", "target": "reservoir.input.demand_outflow"},
            # PID controller controls the reservoir's release
            {"source": "reservoir.state.level", "target": "pid_controller.input.error_source"},
            {"source": "level_sensor_fault.output", "target": "pid_controller.input.current_value_offset"},
            {"source": "pid_controller.state.output", "target": "reservoir.input.release_outflow"},
        ],
        "execution_order": [
            "inflow_agent",
            "demand_agent",
            "level_sensor_fault",
            "pid_controller",
            "reservoir"
        ],
        "logger_config": [
            "reservoir.state.level",
            "pid_controller.state.output",
            "inflow_agent.output",
            "demand_agent.output",
            "level_sensor_fault.output"
        ]
    }

    manager = SimulationManager()
    results = manager.run(config)

    # --- Plotting ---
    plt.figure(figsize=(15, 10))

    plt.subplot(3, 1, 1)
    plt.plot(results['time'], results['reservoir.state.level'], label='Water Level (m)')
    plt.axhline(y=5.0, color='r', linestyle='--', label='Setpoint (5.0m)')
    plt.title('Reservoir Water Level Over Time')
    plt.ylabel('Water Level (m)')
    plt.legend()
    plt.grid(True)

    plt.subplot(3, 1, 2)
    plt.plot(results['time'], results['inflow_agent.output'], label='Inflow (Rainfall)')
    plt.plot(results['time'], results['demand_agent.output'], label='Outflow (Demand)')
    plt.plot(results['time'], results['pid_controller.state.output'], label='Release (PID Controlled)')
    plt.title('Inflows and Outflows')
    plt.ylabel('Flow Rate (m^3/s)')
    plt.legend()
    plt.grid(True)

    plt.subplot(3, 1, 3)
    plt.plot(results['time'], results['level_sensor_fault.output'], label='Sensor Drift (m)')
    plt.title('Fault Agent Output (Sensor Drift)')
    plt.xlabel('Time (s)')
    plt.ylabel('Drift (m)')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.savefig('results/case_04_disturbance_agents.png')
    print("Simulation complete. Plot saved to results/case_04_disturbance_agents.png")

    return results

if __name__ == '__main__':
    run_disturbance_agent_simulation()
