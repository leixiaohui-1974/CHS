import sys
import os
import matplotlib.pyplot as plt
import pandas as pd

# This is a temporary solution to make the SDK accessible to the example script.
# In a real installation, the SDK would be installed as a package.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'water_system_sdk', 'src')))

from water_system_simulator.simulation_manager import SimulationManager
from water_system_simulator.data_processing.processors import NoiseInjector, DataSmoother

def run_body_agent_simulation():
    """
    This function defines the configuration for a closed-loop control system
    using the new "Body Agent" architecture and runs it using the SimulationManager.
    """
    # This configuration dictionary defines the entire simulation.
    body_agent_config = {
        "simulation_params": {
            "total_time": 200,
            "dt": 1.0
        },
        "components": {
            "reservoir_agent_A": {
                "type": "ReservoirBodyAgent",
                "properties": {
                    "core_physics_model": {
                        "type": "ReservoirModel",
                        "params": {"initial_level": 5.0, "area": 1000.0, "max_level": 20.0}
                    },
                    "sensors": {
                        "level_sensor_1": {
                            "type": "LevelSensor",
                            "params": {
                                "pipeline": {
                                    "processors": [
                                        {"type": "NoiseInjector", "params": {"noise_std_dev": 0.15}},
                                        {"type": "DataSmoother", "params": {"window_size": 3}}
                                    ]
                                }
                            }
                        }
                    },
                    "actuators": {
                        "outlet_actuator": {
                            "type": "GateActuator",
                            "params": {"travel_time": 30.0, "response_delay": 2.0, "initial_position": 0.1}
                        }
                    }
                }
            },
            "pid_controller": {
                "type": "PIDController",
                "properties": {
                    "Kp": 0.5,
                    "Ki": 0.05,
                    "Kd": 0.1,
                    "set_point": 15.0,
                    "output_min": 0.0,
                    "output_max": 1.0 # Command for the actuator
                }
            },
            "inflow_disturbance": {
                "type": "TimeSeriesDisturbance",
                "properties": {
                    "times": [0, 50, 150],
                    "values": [10.0, 20.0, 5.0]
                }
            }
        },
        "connections": [
            # The 'connections' are processed at the start of each time step.
            # They copy the final state from a source component of the *previous*
            # time step to the input of a target component for the *current* time step.

            # Connect the inflow disturbance to the reservoir's inflow.
            {
                "source": "inflow_disturbance.output",
                "target": "reservoir_agent_A.core_physics_model.input.inflow"
            },
            # For this example, we assume the actuator's output (0-1 opening)
            # is directly proportional to the outflow. We'll scale it by a factor.
            # Here, we connect it to a temporary input on the reservoir model.
            # A more realistic model would use a proper Gate model to calculate flow from opening and head.
            {
                 "source": "reservoir_agent_A.actuators.outlet_actuator.output",
                 "target": "reservoir_agent_A.core_physics_model.input.release_outflow" # Simplified connection
            }
        ],
        "execution_order": [
            # The 'execution_order' defines the sequence of component actions *within* a time step.
            # This allows for creating explicit data dependencies within the same step.

            # 1. Update the inflow based on the current time.
            {"component": "inflow_disturbance", "method": "step", "args": {"t": "simulation.t", "dt": "simulation.dt"}},

            # 2. PID calculates the gate command based on the *sensed level from the previous step*.
            # The sensor's output is read via the `state` property of the agent.
            {
                "component": "pid_controller",
                "method": "step",
                "args": {"dt": "simulation.dt", "error_source": "reservoir_agent_A.state.level_sensor_1"}
            },

            # 3. The actuator receives the new command from the PID and updates its internal state (e.g., starts moving).
            {
                "component": "reservoir_agent_A.actuators.outlet_actuator",
                "method": "step",
                "args": {"dt": "simulation.dt", "command": "pid_controller.output"}
            },

            # 4. The core physics model evolves. It uses the inflow from this step and the *new* actuator position
            #    (which was connected via the `connections` block before this step).
            {"component": "reservoir_agent_A.core_physics_model", "method": "step", "args": {"dt": "simulation.dt"}},

            # 5. The sensor takes a new measurement of the *updated* physical state. This new sensed value
            #    will be available for the PID controller in the *next* time step.
            {
                "component": "reservoir_agent_A.sensors.level_sensor_1",
                "method": "step",
                "args": {"true_value": "reservoir_agent_A.core_physics_model.output"}
            },
        ],
        "logger_config": [
            "reservoir_agent_A.core_physics_model.state.level", # True physical state
            "reservoir_agent_A.sensors.level_sensor_1.output",   # Sensed state
            "reservoir_agent_A.actuators.outlet_actuator.output",# Actuator's actual position/output
            "pid_controller.output",                             # PID command
            "pid_controller.set_point"                           # Target setpoint
        ]
    }

    # --- Run the simulation ---
    manager = SimulationManager(config=body_agent_config)
    # The new manager doesn't need a separate load_config call
    # manager.load_config(body_agent_config)
    results_df = manager.run()

    return results_df

def plot_body_agent_results(df):
    """Plots the simulation results."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)

    # Plot 1: Water Levels
    ax1.plot(df['time'], df['reservoir_agent_A.core_physics_model.state.level'], label='True Water Level', linewidth=2)
    ax1.plot(df['time'], df['reservoir_agent_A.sensors.level_sensor_1.output'], label='Sensed Water Level', linestyle=':', marker='.', markersize=4)
    ax1.axhline(y=df['pid_controller.set_point'].iloc[0], color='r', linestyle='--', label='Setpoint')
    ax1.set_ylabel('Water Level (m)')
    ax1.set_title('Body Agent Control Simulation: Reservoir Level')
    ax1.legend()
    ax1.grid(True)

    # Plot 2: Actuator and Controller
    ax2.plot(df['time'], df['pid_controller.output'], label='PID Command (Target Opening)', linestyle='--')
    ax2.plot(df['time'], df['reservoir_agent_A.actuators.outlet_actuator.output'], label='Actuator Position (Actual Opening)', linewidth=2)
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Gate Opening (0-1)')
    ax2.set_title('Controller and Actuator Behavior')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    plt.savefig('results/case_25_body_agent_control.png')
    print("Plot saved to results/case_25_body_agent_control.png")
    # plt.show()

if __name__ == "__main__":
    # Ensure the results directory exists
    if not os.path.exists('results'):
        os.makedirs('results')

    simulation_results = run_body_agent_simulation()
    print("Simulation finished. Results:")
    print(simulation_results.head())
    plot_body_agent_results(simulation_results)
