import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
import pandas as pd
import sys
import os

# This is a simple way to make the SDK accessible to the script.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..')))

from chs_sdk.core.host import AgentKernel as Host
from chs_sdk.modules.modeling.storage_models import FixedLinearTank
from chs_sdk.modules.modeling.control_structure_models import HydropowerStationModel
from water_system_sdk.docs.guide.source.project_utils import ModelAgent

def run_simulation():
    """
    This script demonstrates the simulation of a hydropower station,
    showing how flow and power generation change with different
    guide vane openings and a decreasing reservoir level.
    """
    host = Host()

    # 1. 创建组件 - 使用FixedLinearTank确保水量平衡计算正确
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='UpstreamReservoir',
        model_class=FixedLinearTank,
        initial_level=100.0,
        area=200000)  # 增大水库面积，减缓水位下降速度
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='HydroStation',
        model_class=HydropowerStationModel,
        max_flow_area=15.0,  # 减小最大流量面积，使控制更明显
        discharge_coeff=0.9,
        efficiency=0.85)

    # 2. 建立连接
    reservoir_agent = host._agents['UpstreamReservoir']
    hydro_station_agent = host._agents['HydroStation']

    reservoir_agent.subscribe(f"{hydro_station_agent.agent_id}/output", 'release_outflow')

    # 3. 运行与手动控制
    num_steps = 48 # 模拟48小时，增加时间分辨率
    dt = 3600.0 # 时间步长为1小时（3600秒）
    results = []
    host.start(time_step=dt)
    for i in range(num_steps):
        # 手动设置导叶开度 - 更平滑的控制策略
        if i < 12:
            vane_opening = 0.2  # 第0-11小时，20%开度
        elif i < 24:
            vane_opening = 0.4  # 第12-23小时，40%开度
        elif i < 36:
            vane_opening = 0.8  # 第24-35小时，80%开度
        else:
            vane_opening = 0.0  # 最后12小时，关闭

        # 设置水电站的输入
        hydro_station_agent.input_values['vane_opening'] = vane_opening
        hydro_station_agent.input_values['upstream_level'] = reservoir_agent.model.output
        hydro_station_agent.input_values['downstream_level'] = 15.0 # 降低尾水位，增加有效水头

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

    # 添加导叶开度数据用于绘图
    vane_openings = []
    for i in range(num_steps):
        if i < 12:
            vane_openings.append(0.2)   # 20%开度
        elif i < 24:
            vane_openings.append(0.4)   # 40%开度
        elif i < 36:
            vane_openings.append(0.8)   # 80%开度
        else:
            vane_openings.append(0.0)   # 关闭
    
    results_df['vane_opening'] = vane_openings

    # 创建2x2子图布局
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('第九章: 水电站发电仿真', fontsize=16)

    # 图1：上游水库水位
    ax1.plot(results_df['time'], results_df['UpstreamReservoir.value'], 'b-', linewidth=2, label='上游水库水位')
    ax1.set_ylabel('水位 (m)')
    ax1.set_title('上游水库水位变化')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 图2：导叶开度
    ax2.step(results_df['time'], results_df['vane_opening'] * 100, 'r-', linewidth=2, where='post', label='导叶开度')
    ax2.set_ylabel('开度 (%)')
    ax2.set_title('导叶开度控制')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # 图3：水电站流量
    ax3.plot(results_df['time'], results_df['HydroStation.flow'], 'c-', linewidth=2, label='水电站流量')
    ax3.set_ylabel('流量 (m^3/s)')
    ax3.set_xlabel('时间 (h)')
    ax3.set_title('水电站流量变化')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # 图4：水电站发电功率
    ax4.plot(results_df['time'], results_df['HydroStation.power'] / 1e6, 'm-', linewidth=2, label='发电功率')
    ax4.set_ylabel('功率 (MW)')
    ax4.set_xlabel('时间 (h)')
    ax4.set_title('发电功率变化')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

if __name__ == "__main__":
    run_simulation()
