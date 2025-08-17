import matplotlib.pyplot as plt
import numpy as np

# This is a simple way to make the SDK accessible to the script.
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from chs_sdk.core.host import Host
from chs_sdk.modules.modeling.storage_models import LinearTank, MuskingumChannelModel
from chs_sdk.modules.modeling.control_structure_models import HydropowerStationModel

def run_simulation():
    """
    This script simulates a cascade of two hydropower stations to demonstrate
    the hydraulic linkage and time lag caused by the connecting river reach.
    """
    host = Host()

    # 1. 创建组件
    res1 = LinearTank(name='Reservoir1', area=5e6, initial_level=100.0)
    hs1 = HydropowerStationModel(name='HydroStation1', max_flow_area=50.0, discharge_coeff=0.9, efficiency=0.85)

    reach = MuskingumChannelModel(name='RiverReach', K=6*3600.0, x=0.2, dt=1800.0, initial_inflow=10, initial_outflow=10) # 6小时传播时间

    res2 = LinearTank(name='Reservoir2', area=4e6, initial_level=50.0)
    hs2 = HydropowerStationModel(name='HydroStation2', max_flow_area=50.0, discharge_coeff=0.9, efficiency=0.85)

    # 2. 添加到主机
    host.add_agents([res1, hs1, reach, res2, hs2])

    # 3. 连接
    # 上游梯级
    hs1.set_input('upstream_level', res1.get_port('level'))
    hs1.set_input('downstream_level', 55.0) # 假设上游尾水位
    host.add_connection('HydroStation1', 'flow', 'Reservoir1', 'release_outflow')
    # 梯级间连接
    host.add_connection('HydroStation1', 'flow', 'RiverReach', 'inflow')
    host.add_connection('RiverReach', 'outflow', 'Reservoir2', 'inflow')
    # 下游梯级
    hs2.set_input('upstream_level', res2.get_port('level'))
    hs2.set_input('downstream_level', 15.0) # 假设下游尾水位
    host.add_connection('HydroStation2', 'flow', 'Reservoir2', 'release_outflow')

    # 4. 仿真循环与开环调度
    dt_seconds = 1800.0
    num_steps = int(48 * 3600 / dt_seconds) # 模拟48小时

    print("Running cascade hydropower simulation...")
    for i in range(num_steps):
        current_hour = (i * dt_seconds / 3600) % 24

        # 预设的调度计划
        if 8 <= current_hour < 20:
            # 白天高峰发电
            vane_opening = 0.9
        else:
            # 夜间低谷发电
            vane_opening = 0.2

        hs1.set_input('vane_opening', vane_opening)
        hs2.set_input('vane_opening', vane_opening) # 下游尝试执行相同计划

        host.step(dt=dt_seconds)
    print("Simulation finished.")

    # 5. 绘图
    results_df = host.get_datalogger().get_as_dataframe()
    time_hours = results_df.index * dt_seconds / 3600

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    fig.suptitle('第二十六章: 梯级水电站联动仿真', fontsize=16)

    # 图1: 流量对比
    ax1.plot(time_hours, results_df['HydroStation1.flow'], 'b-', label='上游电站出流')
    ax1.plot(time_hours, results_df['RiverReach.outflow'], 'r--', label='下游水库入流 (滞后)')
    ax1.set_ylabel('流量 (m³/s)'); ax1.legend(); ax1.grid(True)

    # 图2: 水位对比
    ax2.plot(time_hours, results_df['Reservoir1.level'], 'b-', label='上游水库水位')
    ax2b = ax2.twinx()
    ax2b.plot(time_hours, results_df['Reservoir2.level'], 'g--', label='下游水库水位 (右轴)')
    ax2.set_xlabel('时间 (小时)'); ax2.set_ylabel('上游水位 (m)'); ax2b.set_ylabel('下游水位 (m)')

    # 合并图例
    lines, labels = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2b.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='best')
    ax2.grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95]); plt.show()

if __name__ == "__main__":
    run_simulation()
