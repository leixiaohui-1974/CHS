import matplotlib.pyplot as plt
from chs_sdk.core.host import Host
from chs_sdk.modules.modeling.storage_models import FirstOrderStorageModel
from chs_sdk.modules.modeling.control_structure_models import HydropowerStationModel

def run_simulation():
    """
    This script demonstrates the simulation of a hydropower station,
    showing how flow and power generation change with different
    guide vane openings and a decreasing reservoir level.
    """
    host = Host()

    # 1. 创建组件
    # 发电水库
    reservoir = FirstOrderStorageModel(name='UpstreamReservoir', initial_value=100.0, area=50000)

    # 水电站模型
    hydro_station = HydropowerStationModel(
        name='HydroStation',
        max_flow_area=20.0,    # 最大过流面积
        discharge_coeff=0.9, # 流量系数
        efficiency=0.85      # 综合效率
    )

    # 2. 添加到主机
    host.add_agent(reservoir)
    host.add_agent(hydro_station)

    # 3. 连接
    # 水电站的泄流量是水库的出流
    host.add_connection('HydroStation', 'value', 'UpstreamReservoir', 'outflow')

    # 4. 运行与手动控制
    num_steps = 24 # 模拟24小时
    downstream_level = 20.0 # 假设尾水位恒定

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
        hydro_station.set_input('vane_opening', vane_opening)
        hydro_station.set_input('upstream_level', reservoir.get_port('value').value)
        hydro_station.set_input('downstream_level', downstream_level)

        # 运行一个步长
        host.step(dt=3600.0) # 时间步长为1小时（3600秒）

    # 5. 绘图
    results_df = host.get_datalogger().get_as_dataframe()
    print("仿真结果 (前5行):")
    print(results_df.head())

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12), sharex=True)
    fig.suptitle('第九章: 水电站发电仿真', fontsize=16)

    # 图1：上游水库水位
    ax1.plot(results_df.index, results_df['UpstreamReservoir.value'], 'b-', label='上游水库水位')
    ax1.set_ylabel('水位 (m)')
    ax1.legend()
    ax1.grid(True)

    # 图2：水电站流量
    ax2.plot(results_df.index, results_df['HydroStation.flow'], 'c-', label='水电站流量')
    ax2.set_ylabel('流量 (m³/s)')
    ax2.legend()
    ax2.grid(True)

    # 图3：水电站发电功率
    ax3.plot(results_df.index, results_df['HydroStation.power'], 'm-', label='发电功率')
    ax3.set_ylabel('功率 (Watts)')
    ax3.set_xlabel('时间 (小时)')
    ax3.legend()
    ax3.grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

if __name__ == "__main__":
    run_simulation()
