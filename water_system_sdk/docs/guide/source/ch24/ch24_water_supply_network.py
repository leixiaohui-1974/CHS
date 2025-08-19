import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from chs_sdk.core.host import AgentKernel as Host
from chs_sdk.modules.modeling.storage_models import LinearTank
from chs_sdk.modules.modeling.control_structure_models import PumpStationModel
from chs_sdk.modules.disturbances.timeseries_disturbance import TimeSeriesDisturbance
from water_system_sdk.docs.guide.source.project_utils import ModelAgent

def run_simulation():
    """
    This script simulates a simplified urban water supply system, demonstrating
    multi-level control (on/off pump logic) to maintain the level of an
    elevated tank that serves a fluctuating city demand.
    """
    host = Host()

    # 1. 创建物理组件
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='Source',
        model_class=LinearTank,
        initial_level=10.0,
        area=1e5)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='Pump',
        model_class=PumpStationModel,
        num_pumps_total=1,
        curve_coeffs=[-0.001, 0.05, 80])
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='ElevatedTank',
        model_class=LinearTank,
        initial_level=55.0,
        area=1000)

    demand_times = np.arange(0, 24 * 3600, 3600)
    demand_base = -8 + 4 * np.sin(2 * np.pi * demand_times / (24 * 3600))
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='Demand',
        model_class=TimeSeriesDisturbance,
        times=demand_times,
        values=demand_base)

    # 2. 建立连接
    source_reservoir_agent = host._agents['Source']
    pump_agent = host._agents['Pump']
    elevated_tank_agent = host._agents['ElevatedTank']
    city_demand_agent = host._agents['Demand']

    elevated_tank_agent.subscribe(f"{pump_agent.agent_id}/output", 'inflow')
    elevated_tank_agent.subscribe(f"{city_demand_agent.agent_id}/output", 'release_outflow')
    source_reservoir_agent.subscribe(f"{pump_agent.agent_id}/output", 'release_outflow')

    # 3. 仿真循环与多层控制
    num_steps = 24 * 60
    dt = 60.0
    pump_on = True
    results = []
    host.start(time_step=dt)

    for i in range(num_steps):
        tank_level = elevated_tank_agent.model.output

        if tank_level < 52.0:
            pump_on = True
        elif tank_level > 58.0:
            pump_on = False

        pump_agent.input_values['num_pumps_on'] = 1 if pump_on else 0
        pump_agent.input_values['inlet_pressure'] = source_reservoir_agent.model.output
        pump_agent.input_values['outlet_pressure'] = elevated_tank_agent.model.output

        host.tick()

        results.append({
            'time': host.current_time,
            'ElevatedTank.level': tank_level,
            'pump_status': 1 if pump_on else 0,
            'Demand.value': city_demand_agent.model.output
        })

    # 4. 绘图
    results_df = pd.DataFrame(results)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    fig.suptitle('第二十四章: 城市供水系统仿真', fontsize=16)

    ax1.plot(results_df['time'] / 3600, results_df['ElevatedTank.level'], 'b-', label='高架水箱水位')
    ax1.axhline(y=58.0, color='r', linestyle='--', label='水泵关闭水位')
    ax1.axhline(y=52.0, color='g', linestyle='--', label='水泵开启水位')
    ax1.set_ylabel('水位 (m)')
    ax1.legend(); ax1.grid(True)

    ax2.plot(results_df['time'] / 3600, results_df['pump_status'], 'm-', drawstyle='steps-post', label='水泵状态 (On/Off)')
    ax2.set_ylabel('水泵状态'); ax2.legend(loc='upper left');

    ax2b = ax2.twinx()
    ax2b.plot(results_df['time'] / 3600, results_df['Demand.value'].abs(), 'c:', label='城市需水量')
    ax2b.set_ylabel('流量 (m³/s)'); ax2b.legend(loc='upper right');
    ax2.set_xlabel('时间 (小时)')
    ax2.grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95]); plt.show()

if __name__ == "__main__":
    run_simulation()
