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
    This script simulates an urban drainage system, where a pump station
    is activated to prevent a detention pond from overflowing during a
    heavy storm event.
    """
    host = Host()

    # 1. 定义降雨事件 (mm/hr)
    rainfall_times = np.array([0, 1, 2, 3, 4, 5, 6]) * 3600 # 秒
    rainfall_intensity = [0, 10, 50, 30, 15, 5, 0] # mm/hr
    rainfall = TimeSeriesDisturbance(name='Rainfall', times=rainfall_times, values=rainfall_intensity)

    # 2. 创建物理组件
    catchment_area_km2 = 10.0
    runoff_coeff = 0.6 # 径流系数

    pond = LinearTank(name='DetentionPond', area=1e5, initial_level=2.0, max_level=5.0)
    pump = PumpStationModel(name='DrainagePump', num_pumps_total=3, curve_coeffs=[-0.001, 0.02, 25])

    # 3. 添加到主机
    host.add_agents([rainfall, pond, pump])

    # 4. 仿真循环与控制逻辑
    num_steps = 12 * 60 # 模拟12小时，每分钟一步
    dt = 60.0 # 秒
    pump_on_count = 0
    pump_status_history = []

    print("Running urban drainage simulation...")
    for i in range(num_steps):
        # 简化版产流计算
        current_rainfall_mmhr = rainfall.get_port('value').value
        # mm/hr -> m/s
        runoff_m3s = current_rainfall_mmhr / 1000 / 3600 * (catchment_area_km2 * 1e6) * runoff_coeff
        pond.set_input('inflow', runoff_m3s)

        # 泵站启停控制逻辑
        pond_level = pond.get_port('level').value
        if pond_level > 4.5: # 警戒水位
            pump_on_count = 3 # 全开
        elif pond_level < 2.5: # 安全水位
            pump_on_count = 0 # 全关

        pump.set_input('num_pumps_on', pump_on_count)
        pump.set_input('inlet_level', pond_level)
        pump.set_input('outlet_level', 3.0) # 假设外河水位恒定

        pump_status_history.append(pump_on_count)

        host.step(dt)
    print("Simulation finished.")

    # 5. 绘图
    results_df = host.get_datalogger().get_as_dataframe()
    results_df['pump_status'] = pump_status_history

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    fig.suptitle('第二十五章: 城市排水防涝仿真', fontsize=16)

    # 图1: 调蓄池水位
    ax1.plot(results_df.index / 60, results_df['DetentionPond.level'], 'b-', label='调蓄池水位')
    ax1.axhline(y=4.5, color='r', linestyle='--', label='泵站启动水位')
    ax1.axhline(y=2.5, color='g', linestyle='--', label='泵站关闭水位')
    ax1.set_ylabel('水位 (m)'); ax1.legend(); ax1.grid(True)

    # 图2: 降雨与泵站流量
    # Note: We need to reconstruct the rainfall time series for plotting as the disturbance agent doesn't log its own history.
    rain_plot_vals = [rainfall.get_value_at_time(t*dt) for t in results_df.index]
    ax2.bar(results_df.index / 60, rain_plot_vals, width=1.0, color='c', alpha=0.5, label='降雨强度 (mm/hr)')
    ax2.set_ylabel('降雨强度', color='c'); ax2.tick_params(axis='y', labelcolor='c')
    ax2.legend(loc='upper left')

    ax2b = ax2.twinx()
    ax2b.plot(results_df.index / 60, results_df['DrainagePump.flow'], 'm--', label='泵站排出流量 (m³/s)')
    ax2b.set_ylabel('流量', color='m'); ax2b.tick_params(axis='y', labelcolor='m')
    ax2b.legend(loc='upper right')
    ax2.set_xlabel('时间 (分钟)')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95]); plt.show()


if __name__ == "__main__":
    run_simulation()
