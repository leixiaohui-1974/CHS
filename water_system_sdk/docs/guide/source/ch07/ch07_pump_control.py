import matplotlib.pyplot as plt
import pandas as pd

from chs_sdk.core.host import AgentKernel as Host
from chs_sdk.modules.modeling.storage_models import LinearTank
from chs_sdk.modules.modeling.control_structure_models import PumpStationModel
from chs_sdk.modules.disturbances.predefined import Disturbance
from water_system_sdk.docs.guide.source.project_utils import ModelAgent

def run_simulation():
    """
    This script demonstrates on-off control of a pump station to transfer
    water from a low-level sump to a high-level reservoir.
    """
    host = Host()

    # 1. 创建组件
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='Sump',
        model_class=LinearTank,
        initial_level=1.5,
        area=200)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='Reservoir',
        model_class=LinearTank,
        initial_level=20.0,
        area=1000)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='PumpStation',
        model_class=PumpStationModel,
        num_pumps_total=1,
        curve_coeffs=[-0.005, 0.1, 50])
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='SumpInflow',
        model_class=Disturbance,
        signal_type='constant',
        value=10.0)

    # 2. 建立连接
    sump_agent = host._agents['Sump']
    reservoir_agent = host._agents['Reservoir']
    pump_station_agent = host._agents['PumpStation']
    sump_inflow_agent = host._agents['SumpInflow']

    sump_agent.subscribe(f"{sump_inflow_agent.agent_id}/output", 'inflow')
    reservoir_agent.subscribe(f"{pump_station_agent.agent_id}/output", 'inflow')
    sump_agent.subscribe(f"{pump_station_agent.agent_id}/output", 'release_outflow') # Using release_outflow for pumped water

    # 3. 运行与手动控制
    num_steps = 200
    dt = 1.0
    results = []
    host.start(time_step=dt)
    for i in range(num_steps):
        # 获取当前集水池水位
        sump_level = sump_agent.model.output
        reservoir_level = reservoir_agent.model.output

        # 控制逻辑
        num_pumps_on = pump_station_agent.model.num_pumps_on
        if sump_level > 3.0:
            num_pumps_on = 1 # 水位高，开泵
        elif sump_level < 1.0:
            num_pumps_on = 0 # 水位低，关泵

        # 设置泵站的输入
        pump_station_agent.input_values['num_pumps_on'] = num_pumps_on
        pump_station_agent.input_values['inlet_pressure'] = sump_level
        pump_station_agent.input_values['outlet_pressure'] = reservoir_level

        host.tick()

        results.append({
            'time': host.current_time,
            'Sump.value': sump_level,
            'Reservoir.value': reservoir_level,
            'PumpStation.value': pump_station_agent.model.output,
            'pump_status': num_pumps_on
        })

    # 4. 绘图
    results_df = pd.DataFrame(results)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    fig.suptitle('第七章: 水泵启停控制仿真', fontsize=16)

    # 图1：水位变化
    ax1.plot(results_df['time'], results_df['Sump.value'], label='低位集水池水位')
    ax1.axhline(y=3.0, color='r', linestyle='--', label='开泵水位 (3m)')
    ax1.axhline(y=1.0, color='g', linestyle='--', label='关泵水位 (1m)')
    ax1.set_ylabel('水位 (m)')
    ax1.legend()
    ax1.grid(True)

    ax1b = ax1.twinx()
    ax1b.plot(results_df['time'], results_df['Reservoir.value'], 'k:', label='高位水库水位')
    ax1b.set_ylabel('高位水库水位 (m)')
    ax1b.legend(loc='upper right')

    # 图2：水泵状态和流量
    ax2.plot(results_df['time'], results_df['pump_status'], 'm-', drawstyle='steps-post', label='水泵状态 (On/Off)')
    ax2.set_ylabel('水泵状态')
    ax2.set_xlabel('时间 (秒)')
    ax2.legend(loc='upper left')

    ax2b = ax2.twinx()
    ax2b.plot(results_df['time'], results_df['PumpStation.value'], 'c:', label='泵站流量')
    ax2b.set_ylabel('流量 (m³/s)')
    ax2b.legend(loc='upper right')
    ax2b.grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

if __name__ == "__main__":
    run_simulation()
