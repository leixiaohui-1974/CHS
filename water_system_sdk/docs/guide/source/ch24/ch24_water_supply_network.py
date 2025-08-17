import matplotlib.pyplot as plt
import numpy as np

# This is a simple way to make the SDK accessible to the script.
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from chs_sdk.core.host import Host
from chs_sdk.modules.modeling.storage_models import LinearTank
from chs_sdk.modules.modeling.control_structure_models import PumpStationModel
from chs_sdk.modules.disturbances.predefined import TimeSeriesDisturbance

def run_simulation():
    """
    This script simulates a simplified urban water supply system, demonstrating
    multi-level control (on/off pump logic) to maintain the level of an
    elevated tank that serves a fluctuating city demand.
    """
    host = Host()

    # 1. 创建物理组件
    source_reservoir = LinearTank(name='Source', initial_level=10.0, area=1e5)
    pump = PumpStationModel(name='Pump', num_pumps_total=1, curve_coeffs=[-0.001, 0.05, 80])
    elevated_tank = LinearTank(name='ElevatedTank', initial_level=55.0, area=1000)

    # 模拟城市需水 (负值代表出流)
    demand_times = np.arange(0, 24 * 3600, 3600) # 每小时一个值
    demand_base = -8 + 4 * np.sin(2 * np.pi * demand_times / (24 * 3600))
    city_demand = TimeSeriesDisturbance(name='Demand', times=demand_times, values=demand_base)

    # 2. 添加到主机
    host.add_agents([source_reservoir, pump, elevated_tank, city_demand])

    # 3. 连接
    # 泵的流量进入高架水箱
    host.add_connection('Pump', 'flow', 'ElevatedTank', 'inflow')
    # 城市需水作为高架水箱的出流
    host.add_connection('Demand', 'value', 'ElevatedTank', 'release_outflow')
    # 泵抽水也导致源水库出流（可选，用于完整物质平衡）
    host.add_connection('Pump', 'flow', 'Source', 'release_outflow')

    # 4. 仿真循环与多层控制
    num_steps = 24 * 60 # 模拟24小时，每分钟一步
    pump_on = True
    pump_status_history = []

    print("Running water supply network simulation...")
    for i in range(num_steps):
        # 获取状态
        tank_level = elevated_tank.get_port('level').value

        # 水泵启停控制逻辑 (Hysteresis Control)
        if tank_level < 52.0:
            pump_on = True
        elif tank_level > 58.0:
            pump_on = False

        # 设置泵的边界条件和控制输入
        pump.set_input('num_pumps_on', 1 if pump_on else 0)
        pump.set_input('inlet_level', source_reservoir.level)
        pump.set_input('outlet_level', elevated_tank.level)

        pump_status_history.append(1 if pump_on else 0)

        # 运行一个步长
        host.step(dt=60.0)
    print("Simulation finished.")

    # 5. 绘图
    results_df = host.get_datalogger().get_as_dataframe()
    results_df['pump_status'] = pump_status_history

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    fig.suptitle('第二十四章: 城市供水系统仿真', fontsize=16)

    # 图1: 高架水箱水位
    ax1.plot(results_df.index / 3600, results_df['ElevatedTank.level'], 'b-', label='高架水箱水位')
    ax1.axhline(y=58.0, color='r', linestyle='--', label='水泵关闭水位')
    ax1.axhline(y=52.0, color='g', linestyle='--', label='水泵开启水位')
    ax1.set_ylabel('水位 (m)')
    ax1.legend(); ax1.grid(True)

    # 图2: 水泵状态与流量
    ax2.plot(results_df.index / 3600, results_df['pump_status'], 'm-', drawstyle='steps-post', label='水泵状态 (On/Off)')
    ax2.set_ylabel('水泵状态'); ax2.legend(loc='upper left');

    ax2b = ax2.twinx()
    ax2b.plot(results_df.index / 3600, results_df['Demand.value'].abs(), 'c:', label='城市需水量')
    ax2b.set_ylabel('流量 (m³/s)'); ax2b.legend(loc='upper right');
    ax2.set_xlabel('时间 (小时)')
    ax2.grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95]); plt.show()

if __name__ == "__main__":
    run_simulation()
