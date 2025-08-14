import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Add the 'src' directory of the SDK to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'water_system_sdk', 'src')))

import pandas as pd
from water_system_simulator.simulation_manager import SimulationManager
from water_system_simulator.modeling.base_model import BaseModel

# --- Define a "Ground Truth" Agent for the simulation ---
# This agent needs to be defined locally as it's not part of the core SDK registry.
# The SimulationManager can't build it from config, so we will create an instance
# and pass it to a modified SimulationManager later.
class TrueValueAgent(BaseModel):
    """A simple agent to generate a time-varying ground truth signal."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.time = 0
        self.output = 10.0

    def step(self, dt=1):
        self.time += dt
        self.output = 10.0 + 5.0 * np.sin(self.time / 20)
        return self.output

    def get_state(self):
        return {'value': self.output}

# --- Main simulation logic ---
if __name__ == "__main__":
    # The SimulationManager expects all components to be defined in the config.
    # However, our TrueValueAgent is defined locally. This is a common issue in
    # simulation setups. A robust way is to instantiate it and manually add it
    # to the manager's component list after building from config.

    # 1. Define the simulation configuration dictionary
    simulation_config = {
        "simulation_params": {
            "total_time": 200,
            "dt": 1.0
        },
        "components": {
            "sensor_cluster_1": {
                "type": "SensorClusterAgent",
                "properties": {"num_sensors": 1, "noise_std_dev": 1.5, "bias": -0.5}
            },
            "sensor_cluster_2": {
                "type": "SensorClusterAgent",
                "properties": {"num_sensors": 1, "noise_std_dev": 1.0, "bias": 0.8}
            },
            "edge_pump_station": {
                "type": "PumpStationAgent",
                "properties": {
                    "pipeline": {
                        "processors": [{
                            "type": "DataSmoother",
                            "params": {"window_size": 5}
                        }]
                    }
                }
            },
            "center_fusion_agent": {
                "type": "CentralDataFusionAgent",
                "properties": {
                    "pipeline": {
                        "processors": [{
                            "type": "DataFusionEngine",
                            "params": {"mode": "weighted_average", "weights": {"sensor_1": 0.6, "sensor_2": 0.4}}
                        }]
                    }
                }
            }
        },
        "execution_order": [
            # Note: We will manually execute the true_value_agent and pass its output
            # to the sensor clusters, as it's not managed by the SimulationManager.
            {"component": "sensor_cluster_1", "method": "step", "args": {"true_value": "placeholder"}},
            {"component": "sensor_cluster_2", "method": "step", "args": {"true_value": "placeholder"}},
            {"component": "edge_pump_station", "method": "step", "args": {"raw_sensor_input": "sensor_cluster_1.output"}},
            {"component": "center_fusion_agent", "method": "step", "args": {
                "sensor_1": "sensor_cluster_1.output.sensor_1",
                "sensor_2": "sensor_cluster_2.output.sensor_1"
            }},
        ],
        "logger_config": [
            "sensor_cluster_1.output.sensor_1",
            "sensor_cluster_2.output.sensor_1",
            "edge_pump_station.output.sensor_1",
            "center_fusion_agent.output.fused_value"
        ]
    }

    # 2. Instantiate the manager and the custom agent
    manager = SimulationManager()
    true_value_agent = TrueValueAgent(name="true_value")

    # 3. Manually run the simulation loop to handle the custom agent
    history = []
    total_time = simulation_config["simulation_params"]["total_time"]
    dt = simulation_config["simulation_params"]["dt"]

    # Load the config into the manager
    manager.load_config(simulation_config)

    for t in np.arange(0, total_time, dt):
        # A. Step the true value agent
        current_true_value = true_value_agent.step(dt)

        # B. Get sensor readings by manually stepping them
        s1_readings = manager.components["sensor_cluster_1"].step(true_value=current_true_value)
        s2_readings = manager.components["sensor_cluster_2"].step(true_value=current_true_value)

        # C. Step the edge and center agents
        edge_output = manager.components["edge_pump_station"].step(raw_sensor_input=s1_readings)
        center_output = manager.components["center_fusion_agent"].step(
            sensor_1=s1_readings['sensor_1'],
            sensor_2=s2_readings['sensor_1']
        )

        # D. Log data
        log_entry = {
            "time": t,
            "true_value": current_true_value,
            "sensor_1_raw": s1_readings['sensor_1'],
            "sensor_2_raw": s2_readings['sensor_1'],
            "edge_estimate": edge_output.get('sensor_1', np.nan),
            "center_estimate": center_output.get('fused_value', np.nan)
        }
        history.append(log_entry)

    log_df = pd.DataFrame(history)

    # 4. Plotting
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(15, 8))

    ax.plot(log_df['time'], log_df['true_value'], 'r-', label='True Value', linewidth=2.5)
    ax.scatter(log_df['time'], log_df['sensor_1_raw'], c='gray', marker='.', alpha=0.6, label='Raw Sensor 1')
    ax.scatter(log_df['time'], log_df['sensor_2_raw'], c='dimgray', marker='x', alpha=0.6, label='Raw Sensor 2')
    ax.plot(log_df['time'], log_df['edge_estimate'], 'y--', label='Edge Estimate (Smoothed)', linewidth=2)
    ax.plot(log_df['time'], log_df['center_estimate'], 'b--', label='Central Estimate (Fused)', linewidth=2.5, dashes=(4, 2))

    ax.set_title('Hierarchical Data Fusion: Center vs. Edge', fontsize=16)
    ax.set_xlabel('Time Step', fontsize=12)
    ax.set_ylabel('Value', fontsize=12)
    ax.legend(fontsize=12, loc='upper right')
    ax.grid(True)
    plt.tight_layout()

    output_filename = "hierarchical_data_fusion_comparison.png"
    plt.savefig(output_filename)
    print(f"Plot saved to {output_filename}")

    # To prevent hanging in non-interactive environments
    # plt.show()
