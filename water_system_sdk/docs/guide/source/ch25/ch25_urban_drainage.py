import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from chs_sdk.core.host import AgentKernel as Host
from chs_sdk.modules.modeling.storage_models import LinearTank
from chs_sdk.modules.modeling.control_structure_models import PumpStationModel
from chs_sdk.modules.disturbances.timeseries_disturbance import TimeSeriesDisturbance
from project_utils import ModelAgent

def run_simulation():
    """
    This script simulates an urban drainage system, where a pump station
    is activated to prevent a detention pond from overflowing during a
    heavy storm event.
    """
    host = Host()

    # 1. 定义降雨事件 (mm/hr)
    rainfall_times = np.array([0, 1, 2, 3, 4, 5, 6]) * 3600
    rainfall_intensity = [0, 10, 50, 30, 15, 5, 0]
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='Rainfall',
        model_class=TimeSeriesDisturbance,
        times=rainfall_times,
        values=rainfall_intensity)

    # 2. 创建物理组件
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='DetentionPond',
        model_class=LinearTank,
        area=1e5,
        initial_level=2.0,
        max_level=5.0)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='DrainagePump',
        model_class=PumpStationModel,
        num_pumps_total=3,
        curve_coeffs=[-0.001, 0.02, 25])

    # 3. 建立连接
    rainfall_agent = host._agents['Rainfall']
    pond_agent = host._agents['DetentionPond']
    pump_agent = host._agents['DrainagePump']

    pond_agent.subscribe(f"{pump_agent.agent_id}/output", 'release_outflow')

    # 4. 仿真循环与控制逻辑
    num_steps = 12 * 60
    dt = 60.0
    pump_on_count = 0
    results = []
    catchment_area_km2 = 10.0
    runoff_coeff = 0.6

    host.start(time_step=dt)

    for i in range(num_steps):
        current_rainfall_mmhr = rainfall_agent.model.output
        runoff_m3s = current_rainfall_mmhr / 1000 / 3600 * (catchment_area_km2 * 1e6) * runoff_coeff
        pond_agent.input_values['inflow'] = runoff_m3s

        pond_level = pond_agent.model.output
        if pond_level > 4.5:
            pump_on_count = 3
        elif pond_level < 2.5:
            pump_on_count = 0

        pump_agent.input_values['num_pumps_on'] = pump_on_count
        pump_agent.input_values['inlet_pressure'] = pond_level
        pump_agent.input_values['outlet_pressure'] = 3.0

        host.tick()

        results.append({
            'time': host.current_time,
            'DetentionPond.level': pond_level,
            'DrainagePump.flow': pump_agent.model.output,
            'pump_status': pump_on_count,
            'rainfall': current_rainfall_mmhr
        })

    # 5. 绘图
    results_df = pd.DataFrame(results)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    fig.suptitle('第二十五章: 城市排水防涝仿真', fontsize=16)

    ax1.plot(results_df['time'] / 60, results_df['DetentionPond.level'], 'b-', label='调蓄池水位')
    ax1.axhline(y=4.5, color='r', linestyle='--', label='泵站启动水位')
    ax1.axhline(y=2.5, color='g', linestyle='--', label='泵站关闭水位')
    ax1.set_ylabel('水位 (m)'); ax1.legend(); ax1.grid(True)

    ax2.bar(results_df['time'] / 60, results_df['rainfall'], width=1.0, color='c', alpha=0.5, label='降雨强度 (mm/hr)')
    ax2.set_ylabel('降雨强度', color='c'); ax2.tick_params(axis='y', labelcolor='c')
    ax2.legend(loc='upper left')

    ax2b = ax2.twinx()
    ax2b.plot(results_df['time'] / 60, results_df['DrainagePump.flow'], 'm--', label='泵站排出流量 (m³/s)')
    ax2b.set_ylabel('流量', color='m'); ax2b.tick_params(axis='y', labelcolor='m')
    ax2b.legend(loc='upper right')
    ax2.set_xlabel('时间 (分钟)')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95]); plt.show()


if __name__ == "__main__":
    run_simulation()
