import json
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# This is a simple way to make the SDK accessible to the script.
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from chs_sdk.modules.hydrology.core import Basin
from chs_sdk.core.host import Host
from chs_sdk.modules.modeling.storage_models import NonlinearTank
from chs_sdk.modules.modeling.control_structure_models import GateModel
from chs_sdk.modules.modeling.storage_models import MuskingumChannelModel
from chs_sdk.modules.control.rule_based_controller import RuleBasedOperationalController

def run_forecast_model():
    """Runs the hydrological forecast to get the inflow hydrograph."""
    print("--- Running Stage 1: Hydrological Forecast ---")
    source_dir = os.path.dirname(__file__)
    with open(os.path.join(source_dir, 'ch27_hydrology_topology.json'), 'r') as f:
        topology_data = json.load(f)
    with open(os.path.join(source_dir, 'ch27_hydrology_parameters.json'), 'r') as f:
        params_data = json.load(f)
    with open(os.path.join(source_dir, 'ch27_hydrology_timeseries.json'), 'r') as f:
        timeseries_data = json.load(f)

    basin = Basin(topology_data, params_data, timeseries_data)
    results = basin.run_simulation()
    # The result is the flow at the sink node, which is our reservoir inflow
    forecasted_inflow = results['ReservoirInflow']
    print("Forecast complete.")
    return forecasted_inflow

def run_dispatch_simulation(forecasted_inflow):
    """Runs the dispatch simulation using the forecast."""
    print("\n--- Running Stage 2: Flood Control Dispatch Simulation ---")
    host = Host()

    # 1. Create components
    level_volume_curve = np.array([[20.0, 25.0, 30.0, 35.0], [0, 5e6, 12e6, 25e6]])
    reservoir = NonlinearTank(name='FloodControlReservoir', level_to_volume=level_volume_curve, initial_level=22.0)
    gate = GateModel(name='SpillwayGate', gate_width=10.0, discharge_coeff=0.8)
    reach = MuskingumChannelModel(name='DownstreamReach', K=3*3600, x=0.2, dt=3600)

    # 2. Define dispatch rules
    forecast_peak = np.max(forecasted_inflow)
    rules = [
        {"if": [{"variable": "FloodControlReservoir.level", "operator": ">", "value": 32.0}],
         "then": {"gate_opening": 1.0}}, # Emergency spill
        {"if": [{"variable": "forecast.peak", "operator": ">", "value": 300},
                {"variable": "FloodControlReservoir.level", "operator": ">", "value": 24.0}],
         "then": {"gate_opening": 0.4}}, # Proactive release
    ]
    default_actions = {"gate_opening": 0.0}
    dispatcher = RuleBasedOperationalController('Dispatcher', rules, default_actions)

    # 3. Add agents and connect
    host.add_agents([reservoir, gate, reach, dispatcher])
    host.add_connection('Dispatcher', 'gate_opening', 'SpillwayGate', 'command')
    gate.set_input('upstream_level', reservoir.get_port('level'))
    gate.set_input('downstream_level', 10.0) # Assume constant tailwater
    host.add_connection('SpillwayGate', 'flow', 'FloodControlReservoir', 'release_outflow')
    host.add_connection('SpillwayGate', 'flow', 'DownstreamReach', 'inflow')

    # 4. Run simulation
    num_steps = len(forecasted_inflow)
    dt = 3600.0

    for i in range(num_steps):
        # Set the forecasted inflow for the current step
        reservoir.set_input('inflow', forecasted_inflow[i])

        # Provide current state to the dispatcher
        current_state = {
            "FloodControlReservoir.level": reservoir.level,
            "forecast.peak": forecast_peak
        }
        dispatcher.step(system_state=current_state)

        host.step(dt)

    return host.get_datalogger().get_as_dataframe()

def main():
    # Stage 1: Get the forecast
    forecasted_inflow = run_forecast_model()

    # Stage 2: Run the dispatch simulation
    dispatch_results_df = run_dispatch_simulation(forecasted_inflow)

    # --- Plotting ---
    print("\n--- Plotting Results ---")
    time_hours = np.arange(len(forecasted_inflow))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    fig.suptitle('第二十七章: 预报-调度联动防洪仿真', fontsize=16)

    # Plot 1: Inflows
    ax1.plot(time_hours, forecasted_inflow, 'b-', label='水库天然入流 (预报)')
    ax1.plot(time_hours, dispatch_results_df['SpillwayGate.flow'], 'r--', label='水库下泄流量 (调度后)')
    ax1.set_ylabel('流量 (m³/s)'); ax1.legend(); ax1.grid(True)

    # Plot 2: Reservoir Level
    ax2.plot(time_hours, dispatch_results_df['FloodControlReservoir.level'], 'g-', label='水库水位')
    ax2.axhline(y=32.0, color='red', linestyle='--', label='警戒水位')
    ax2.set_xlabel('时间 (小时)'); ax2.set_ylabel('水位 (m)'); ax2.legend(); ax2.grid(True)

    plt.show()

if __name__ == "__main__":
    main()
