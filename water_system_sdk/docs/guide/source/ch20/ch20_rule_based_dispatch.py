import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))


from chs_sdk.core.host import AgentKernel as Host
from chs_sdk.modules.modeling.storage_models import LinearTank
from chs_sdk.modules.modeling.control_structure_models import SluiceGate, PumpStationModel
from chs_sdk.modules.control.rule_based_controller import RuleBasedOperationalController
from chs_sdk.modules.disturbances.timeseries_disturbance import TimeSeriesDisturbance
from water_system_sdk.docs.guide.source.project_utils import ModelAgent

def run_simulation():
    """
    This script demonstrates how to use a RuleBasedOperationalController
    to implement operational dispatch logic for a reservoir.
    """
    host = Host()

    # 1. 创建组件
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='MainReservoir',
        model_class=LinearTank,
        area=2000.0,
        initial_level=5.0)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='InletGate',
        model_class=SluiceGate,
        gate_width=2.0,
        discharge_coeff=0.8,
        slew_rate=1.0/60.0) # Assume 60s travel time
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='OutletPump',
        model_class=PumpStationModel,
        num_pumps_total=1,
        curve_coeffs=[-0.001, 0.05, 20])
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='UpstreamInflow',
        model_class=TimeSeriesDisturbance,
        times=[0, 200, 201, 1000],
        values=[5, 5, 20, 20])

    rules = [
        {"if": [{"variable": "MainReservoir.level", "operator": ">", "value": 15.0}], "then": {"gate_opening": 0.0, "pump_command": 1}},
        {"if": [{"variable": "MainReservoir.level", "operator": "<", "value": 3.0}], "then": {"gate_opening": 1.0, "pump_command": 0}},
    ]
    default_actions = {"gate_opening": 0.5, "pump_command": 0}
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='ReservoirDispatcher',
        model_class=RuleBasedOperationalController,
        rules=rules,
        default_actions=default_actions)

    # 2. 建立连接
    reservoir_agent = host._agents['MainReservoir']
    inlet_gate_agent = host._agents['InletGate']
    outlet_pump_agent = host._agents['OutletPump']
    inflow_disturbance_agent = host._agents['UpstreamInflow']
    dispatcher_agent = host._agents['ReservoirDispatcher']

    inlet_gate_agent.subscribe(f"{dispatcher_agent.agent_id}/gate_opening", 'command')
    outlet_pump_agent.subscribe(f"{dispatcher_agent.agent_id}/pump_command", 'num_pumps_on')

    inlet_gate_agent.input_values['upstream_level'] = 20.0
    inlet_gate_agent.subscribe(f"{reservoir_agent.agent_id}/level", 'downstream_level')

    outlet_pump_agent.subscribe(f"{reservoir_agent.agent_id}/level", 'inlet_pressure')
    outlet_pump_agent.input_values['outlet_pressure'] = 2.0

    reservoir_agent.subscribe(f"{inlet_gate_agent.agent_id}/output", 'gate_inflow')
    reservoir_agent.subscribe(f"{inflow_disturbance_agent.agent_id}/output", 'inflow')
    reservoir_agent.subscribe(f"{outlet_pump_agent.agent_id}/output", 'release_outflow')

    # 3. 运行仿真
    num_steps = 1000
    dt = 1.0
    results = []
    host.start(time_step=dt)
    for i in range(num_steps):
        host.tick()
        results.append({
            'time': host.current_time,
            'MainReservoir.level': reservoir_agent.model.level,
            'ReservoirDispatcher.gate_opening': dispatcher_agent.model.current_actions.get('gate_opening'),
            'ReservoirDispatcher.pump_command': dispatcher_agent.model.current_actions.get('pump_command')
        })

    # 4. 绘图
    results_df = pd.DataFrame(results)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    fig.suptitle('第二十章: 基于规则的水库调度仿真', fontsize=16)

    ax1.plot(results_df['time'], results_df['MainReservoir.level'], 'b-', label='水库水位')
    ax1.axhline(y=15.0, color='r', linestyle='--', label='汛限水位 (15m)')
    ax1.axhline(y=3.0, color='g', linestyle='--', label='兴利水位 (3m)')
    ax1.set_ylabel('水位 (m)')
    ax1.legend(); ax1.grid(True)

    ax2.plot(results_df['time'], results_df['ReservoirDispatcher.gate_opening'], 'c-', label='闸门开度指令')
    ax2.plot(results_df['time'], results_df['ReservoirDispatcher.pump_command'], 'm--', label='水泵开关指令')
    ax2.set_xlabel('时间 (秒)'); ax2.set_ylabel('调度指令'); ax2.legend(); ax2.grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    output_dir = 'results/ch20'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'ch20_rule_based_dispatch.png')
    plt.savefig(output_path)
    plt.close()
    print(f"Plot saved to {output_path}")

if __name__ == "__main__":
    run_simulation()
