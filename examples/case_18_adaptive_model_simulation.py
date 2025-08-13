import yaml
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

# Add the src directory to the Python path
# This allows importing from water_system_simulator
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../water_system_sdk/src')))

from water_system_simulator.simulation_manager import SimulationManager
from water_system_simulator.modeling.base_model import BaseModel
from water_system_simulator.core.datastructures import State, Input
from water_system_simulator.simulation_manager import ComponentRegistry

def run_and_visualize_adaptive_simulation(config_path):
    """
    Runs the adaptive model simulation and visualizes the results.
    """
    # 1. Load configuration from YAML file
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Add a dummy model to the registry for the test
    class SimpleWaterBalanceModel(BaseModel):
        def __init__(self, evaporation_coeff=0.0):
            super().__init__()
            self.params = State(evaporation_coeff=evaporation_coeff)
            self.input = Input(inflow=0)
            self.state = State(storage=0)
            self.output = 0
        def step(self, dt, t):
            storage_change = (self.input.inflow - self.state.storage * self.params.evaporation_coeff) * dt
            self.state.storage += storage_change
            # Add a small base to avoid zero storage issues and make output visible
            self.output = self.state.storage * 0.1 + 10

    if 'SimpleWaterBalanceModel' not in ComponentRegistry._CLASS_MAP:
        ComponentRegistry._CLASS_MAP['SimpleWaterBalanceModel'] = SimpleWaterBalanceModel

    # 2. Initialize and run the simulation
    manager = SimulationManager()
    results_df = manager.run(config)

    # 3. Plot the results
    fig, axs = plt.subplots(4, 1, figsize=(12, 16), sharex=True)
    fig.suptitle('Adaptive Model Simulation Results', fontsize=16)

    # Plot 1: Inflow and Trigger
    axs[0].plot(results_df['time'], results_df['inflow_source.output'],
                label='Upstream Inflow', color='blue')
    axs[0].set_ylabel('Flow (m^3/s)')
    axs[0].set_title('Inflow & Model Switch Trigger')
    axs[0].axhline(1000, color='r', linestyle='--', label='Switch Threshold')
    axs[0].legend()
    axs[0].grid(True)

    # Plot 2: River Outflow and Active Model
    ax2_twin = axs[1].twinx()
    p1, = axs[1].plot(results_df['time'], results_df['long_river_A.output'],
                label='River Outflow (from Active Model)', color='green')

    model_id_map = { "daily_balance_model": 0, "hourly_flood_model": 1 }
    numeric_active_model = results_df['long_river_A.active_dynamic_model_id'].map(model_id_map)
    p2, = ax2_twin.plot(results_df['time'], numeric_active_model,
                label='Active Model', color='black', drawstyle='steps-post', alpha=0.6)

    axs[1].set_ylabel('Flow (m^3/s)')
    axs[1].set_title('River Outflow & Active Model')
    axs[1].grid(True)
    ax2_twin.set_ylabel('Active Model')
    ax2_twin.set_yticks([0, 1])
    ax2_twin.set_yticklabels(['Balance', 'Flood'])
    axs[1].legend(handles=[p1, p2], loc='upper left')


    # Plot 3: Muskingum K Parameter
    axs[2].plot(results_df['time'], results_df['long_river_A.dynamic_model_bank.hourly_flood_model.params.K'],
                label='K (from param_driver)', color='purple')
    axs[2].set_ylabel('Parameter Value')
    axs[2].set_title('Online Parameter Update (K)')
    axs[2].legend()
    axs[2].grid(True)

    # Plot 4: Muskingum X Parameter
    axs[3].plot(results_df['time'], results_df['long_river_A.dynamic_model_bank.hourly_flood_model.params.X'],
                label='X (fixed update at t=80)', color='orange')
    axs[3].set_xlabel('Time (s)')
    axs[3].set_ylabel('Parameter Value')
    axs[3].set_title('Online Parameter Update (X)')
    axs[3].axvline(80, color='r', linestyle='--', label='Update Trigger')
    axs[3].legend()
    axs[3].grid(True)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    # Save the plot
    output_dir = os.path.join(os.path.dirname(__file__), '../results')
    os.makedirs(output_dir, exist_ok=True)
    plot_path = os.path.join(output_dir, 'case_18_adaptive_simulation.png')
    plt.savefig(plot_path)
    print(f"Plot saved to {plot_path}")
    plt.close()

if __name__ == "__main__":
    config_file = os.path.join(os.path.dirname(__file__), 'case_18_adaptive_model_simulation.yml')
    run_and_visualize_adaptive_simulation(config_file)
