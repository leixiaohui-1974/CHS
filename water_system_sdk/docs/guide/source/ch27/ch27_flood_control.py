import json
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

from chs_sdk.modules.hydrology.core import Basin
from chs_sdk.core.host import AgentKernel as Host
from chs_sdk.modules.modeling.storage_models import NonlinearTank
from chs_sdk.modules.modeling.control_structure_models import SluiceGate
from chs_sdk.modules.modeling.storage_models import MuskingumChannelModel
from chs_sdk.modules.control.rule_based_controller import RuleBasedOperationalController
from water_system_sdk.docs.guide.source.project_utils import ModelAgent, EulerMethod

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
    forecasted_inflow = results['ReservoirInflow']
    print("Forecast complete.")
    return forecasted_inflow

def run_dispatch_simulation(forecasted_inflow):
    """Runs the dispatch simulation using the forecast."""
    print("\n--- Running Stage 2: Flood Control Dispatch Simulation ---")
    host = Host()

    # 1. Create components
    level_volume_curve = np.array([[20.0, 25.0, 30.0, 35.0], [0, 5e6, 12e6, 25e6]])
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='FloodControlReservoir',
        model_class=NonlinearTank,
        level_to_volume=level_volume_curve,
        initial_level=22.0)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='SpillwayGate',
        model_class=SluiceGate,
        gate_width=10.0,
        discharge_coeff=0.8)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='DownstreamReach',
        model_class=MuskingumChannelModel,
        K=3*3600,
        x=0.2,
        dt=3600.0,
        initial_inflow=0,
        initial_outflow=0)

    forecast_peak = np.max(forecasted_inflow)
    rules = [
        {"if": [{"variable": "FloodControlReservoir.level", "operator": ">", "value": 32.0}], "then": {"gate_opening": 1.0}},
        {"if": [{"variable": "forecast.peak", "operator": ">", "value": 300}, {"variable": "FloodControlReservoir.level", "operator": ">", "value": 24.0}], "then": {"gate_opening": 0.4}},
    ]
    default_actions = {"gate_opening": 0.0}
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='Dispatcher',
        model_class=RuleBasedOperationalController,
        rules=rules,
        default_actions=default_actions)

    # 2. Add agents and connect
    reservoir = host._agents['FloodControlReservoir']
    gate = host._agents['SpillwayGate']
    reach = host._agents['DownstreamReach']
    dispatcher = host._agents['Dispatcher']

    gate.subscribe(f"{dispatcher.agent_id}/gate_opening", 'command')
    gate.subscribe(f"{reservoir.agent_id}/level", 'upstream_level')
    gate.input_values['downstream_level'] = 10.0

    reservoir.subscribe(f"{gate.agent_id}/output", 'release_outflow')
    reach.subscribe(f"{gate.agent_id}/output", 'inflow')

    # 3. Run simulation
    num_steps = len(forecasted_inflow)
    dt = 3600.0
    results = []
    host.start(time_step=dt)

    for i in range(num_steps):
        reservoir.input_values['inflow'] = forecasted_inflow[i]

        extra_state = {"forecast.peak": forecast_peak}
        dispatcher.on_execute(host.current_time, host.time_step, extra_state)
        host.message_bus.dispatch()

        reservoir.on_execute(host.current_time, host.time_step)
        host.message_bus.dispatch()

        gate.on_execute(host.current_time, host.time_step)
        host.message_bus.dispatch()

        reach.on_execute(host.current_time, host.time_step)
        host.message_bus.dispatch()

        host.current_time += dt

        results.append({
            'time': host.current_time,
            'SpillwayGate.flow': gate.model.output,
            'FloodControlReservoir.level': reservoir.model.level
        })

    return pd.DataFrame(results)

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

    ax1.plot(time_hours, forecasted_inflow, 'b-', label='水库天然入流 (预报)')
    ax1.plot(time_hours, dispatch_results_df['SpillwayGate.flow'], 'r--', label='水库下泄流量 (调度后)')
    ax1.set_ylabel('流量 (m³/s)'); ax1.legend(); ax1.grid(True)

    ax2.plot(time_hours, dispatch_results_df['FloodControlReservoir.level'], 'g-', label='水库水位')
    ax2.axhline(y=32.0, color='red', linestyle='--', label='警戒水位')
    ax2.set_xlabel('时间 (小时)'); ax2.set_ylabel('水位 (m)'); ax2.legend(); ax2.grid(True)

    plt.show()

if __name__ == "__main__":
    main()
