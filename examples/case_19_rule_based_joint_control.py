import sys
import os
import matplotlib.pyplot as plt

# Make the SDK accessible to the example script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'water_system_sdk', 'src')))

from water_system_simulator.simulation_manager import SimulationManager

def run_rule_based_control_simulation():
    """
    This function defines and runs a simulation demonstrating the
    RuleBasedOperationalController for joint control of a gate and a pump.
    """
    joint_control_config = {
        "simulation_params": {"total_time": 1000, "dt": 1},
        "components": {
            "main_reservoir": {
                "type": "ReservoirModel",
                "params": {"initial_level": 5.0, "area": 2000}
            },
            "inlet_gate": {
                "type": "GateModel",
                "params": {"num_gates": 1, "gate_width": 2.0, "discharge_coeff": 0.6}
            },
            "outlet_pump": {
                "type": "PumpStationModel",
                "params": {"num_pumps_total": 2, "curve_coeffs": [-0.005, 0.1, 50], "initial_num_pumps_on": 0}
            },
            "joint_controller": {
                "type": "RuleBasedOperationalController",
                "params": {
                    "default_actions": {
                        "gate_opening": 0.1,
                        "pump_command": 0
                    },
                    "rules": [
                        {
                            "if": [{"variable": "main_reservoir.state.level", "operator": ">", "value": 15.0}],
                            "then": {"gate_opening": 0.0, "pump_command": 1}
                        },
                        {
                            "if": [{"variable": "main_reservoir.state.level", "operator": "<", "value": 3.0}],
                            "then": {"gate_opening": 1.0, "pump_command": 0}
                        }
                    ]
                }
            },
            "inflow_disturbance": {
                "type": "TimeSeriesDisturbance",
                "params": {
                    "times": [0, 200, 201, 1000],
                    "values": [5, 5, 20, 20] # A sudden increase in inflow to test high-level rule
                }
            }
        },
        "execution_order": [
            # 1. Get external inflow for the current step
            {
                "component": "inflow_disturbance", "method": "step",
                "args": {"t": "simulation.t", "dt": "simulation.dt"}
            },
            # 2. Controller decides actions based on the overall system state
            {
                "component": "joint_controller", "method": "step",
                "args": {"system_state": "simulation.system_state", "dt": "simulation.dt"}
            },
            # 3. Gate receives its command from the controller and calculates its flow
            {
                "component": "inlet_gate", "method": "step",
                "args": {
                    "upstream_level": 20.0, # Assuming a constant upstream source level
                    "gate_opening": "joint_controller.state.gate_opening"
                }
            },
            # 4. Pump receives its command and calculates its flow
            {
                "component": "outlet_pump", "method": "step",
                "args": {
                    "inlet_pressure": "main_reservoir.state.level", # Approximating pressure with level
                    "outlet_pressure": 0, # Pumping out to atmospheric pressure
                    "num_pumps_on": "joint_controller.state.pump_command"
                }
            },
            # 5. Update reservoir level with all inflows and outflows
            {
                "component": "main_reservoir", "method": "step",
                "args": {
                    "dt": "simulation.dt",
                    "inflow": "inlet_gate.output",
                    "release_outflow": "outlet_pump.output",
                    "external_inflow": "inflow_disturbance.output"
                }
            }
        ],
        "logger_config": [
            "main_reservoir.state.level",
            "joint_controller.state.gate_opening",
            "joint_controller.state.pump_command",
            "inlet_gate.state.flow",
            "outlet_pump.state.flow",
            "inflow_disturbance.output"
        ]
    }

    manager = SimulationManager()
    results_df = manager.run(joint_control_config)
    return results_df

def plot_results(df):
    """Plots the simulation results."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)

    # Plot water level and rule thresholds
    ax1.plot(df['time'], df['main_reservoir.state.level'], label='Reservoir Water Level', color='b')
    ax1.axhline(y=15.0, color='r', linestyle='--', label='High Level Threshold (15m)')
    ax1.axhline(y=3.0, color='g', linestyle='--', label='Low Level Threshold (3m)')
    ax1.set_ylabel('Water Level (m)')
    ax1.set_title('Rule-Based Joint Control Simulation')
    ax1.legend()
    ax1.grid(True)

    # Plot control actions
    ax2.plot(df['time'], df['joint_controller.state.gate_opening'], label='Gate Opening Command', color='c')
    ax2.plot(df['time'], df['joint_controller.state.pump_command'], label='Pump On/Off Command', color='m', linestyle='-.')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Control Commands')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    # Ensure results directory exists
    if not os.path.exists('results'):
        os.makedirs('results')
    plt.savefig('results/case_19_rule_based_joint_control.png')
    print("Plot saved to results/case_19_rule_based_joint_control.png")

if __name__ == "__main__":
    simulation_results = run_rule_based_control_simulation()
    print("Simulation finished. Results:")
    print(simulation_results.head())
    plot_results(simulation_results)
