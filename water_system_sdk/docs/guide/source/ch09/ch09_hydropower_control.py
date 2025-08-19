import matplotlib.pyplot as plt
import pandas as pd

from chs_sdk.core.host import AgentKernel as Host
from chs_sdk.modules.modeling.storage_models import LinearTank
from chs_sdk.modules.modeling.control_structure_models import HydropowerStationModel
from project_utils import ModelAgent

def run_simulation():
    """
    This script demonstrates the simulation of a hydropower station,
    showing how flow and power generation change with different
    guide vane openings and a decreasing reservoir level.
    """
    host = Host()

    # 1. 创建组件
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='UpstreamReservoir',
        model_class=LinearTank,
        initial_level=100.0,
        area=50000)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='HydroStation',
        model_class=HydropowerStationModel,
        max_flow_area=20.0,
        discharge_coeff=0.9,
        efficiency=0.85)

    # 2. 建立连接
    reservoir_agent = host._agents['UpstreamReservoir']
    hydro_station_agent = host._agents['HydroStation']

    reservoir_agent.subscribe(f"{hydro_station_agent.agent_id}/output", 'release_outflow')

    # 3. 运行与手动控制
    num_steps = 24 # 模拟24小时
    dt = 3600.0 # 时间步长为1小时（3600秒）
    results = []
    host.start(time_step=dt)
    for i in range(num_steps):
        # 手动设置导叶开度
        if i < 6:
            vane_opening = 0.25 # 第0-5小时，25%开度
        elif i < 12:
            vane_opening = 0.5  # 第6-11小时，50%开度
        elif i < 18:
            vane_opening = 1.0  # 第12-17小时，100%开度
        else:
            vane_opening = 0.0  # 最后6小时，关闭

        # 设置水电站的输入
        hydro_station_agent.input_values['vane_opening'] = vane_opening
        hydro_station_agent.input_values['upstream_level'] = reservoir_agent.model.output
        hydro_station_agent.input_values['downstream_level'] = 20.0 # 假设尾水位恒定

        host.tick()

        results.append({
            'time': host.current_time / 3600, # Convert seconds to hours for plotting
            'UpstreamReservoir.value': reservoir_agent.model.output,
            'HydroStation.flow': hydro_station_agent.model.flow,
            'HydroStation.power': hydro_station_agent.model.power,
        })

    # 4. 绘图
    results_df = pd.DataFrame(results)
    print("仿真结果 (前5行):")
    print(results_df.head())

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12), sharex=True)
    fig.suptitle('第九章: 水电站发电仿真', fontsize=16)

    # 图1：上游水库水位
    ax1.plot(results_df['time'], results_df['UpstreamReservoir.value'], 'b-', label='上游水库水位')
    ax1.set_ylabel('水位 (m)')
    ax1.legend()
    ax1.grid(True)

    # 图2：水电站流量
    ax2.plot(results_df['time'], results_df['HydroStation.flow'], 'c-', label='水电站流量')
    ax2.set_ylabel('流量 (m³/s)')
    ax2.legend()
    ax2.grid(True)

    # 图3：水电站发电功率
    ax3.plot(results_df['time'], results_df['HydroStation.power'], 'm-', label='发电功率')
    ax3.set_ylabel('功率 (Watts)')
    ax3.set_xlabel('时间 (小时)')
    ax3.legend()
    ax3.grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

if __name__ == "__main__":
    run_simulation()
