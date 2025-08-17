import matplotlib.pyplot as plt
from chs_sdk.core.host import Host
from chs_sdk.modules.modeling.storage_models import FirstOrderStorageModel
from chs_sdk.modules.modeling.control_structure_models import PumpStationModel
from chs_sdk.modules.disturbances.predefined import ConstantDisturbance

def run_simulation():
    """
    This script demonstrates on-off control of a pump station to transfer
    water from a low-level sump to a high-level reservoir.
    """
    host = Host()

    # 1. 创建组件
    sump = FirstOrderStorageModel(name='Sump', initial_value=1.5, area=200) # 低位集水池
    reservoir = FirstOrderStorageModel(name='Reservoir', initial_value=20.0, area=1000) # 高位水库

    # 定义泵站，其曲线为 H = -0.005*Q^2 + 0.1*Q + 50
    pump_station = PumpStationModel(name='PumpStation', num_pumps_total=1, curve_coeffs=[-0.005, 0.1, 50])

    # 集水池有一个恒定的入流
    sump_inflow = ConstantDisturbance(name='SumpInflow', constant_value=10.0)

    # 2. 添加到主机
    host.add_agent(sump)
    host.add_agent(reservoir)
    host.add_agent(pump_station)
    host.add_agent(sump_inflow)

    # 3. 连接
    # 集水池的入流
    host.add_connection('SumpInflow', 'value', 'Sump', 'inflow')
    # 泵站的流量成为高位水库的入流
    host.add_connection('PumpStation', 'value', 'Reservoir', 'inflow')
    # 泵站的流量也同时是低位水池的出流
    host.add_connection('PumpStation', 'value', 'Sump', 'outflow')

    # 4. 运行与手动控制
    num_steps = 200
    pump_status_history = []
    for i in range(num_steps):
        # 获取当前集水池水位
        sump_level = sump.get_port('value').value

        # 控制逻辑
        num_pumps_on = pump_station.get_port('num_pumps_on').value
        if sump_level > 3.0:
            num_pumps_on = 1 # 水位高，开泵
        elif sump_level < 1.0:
            num_pumps_on = 0 # 水位低，关泵

        # 设置泵站的输入
        pump_station.set_input('num_pumps_on', num_pumps_on)
        # 扬程 = 出口水位 - 入口水位
        pump_station.set_input('inlet_level', sump_level)
        pump_station.set_input('outlet_level', reservoir.get_port('value').value)

        # 记录状态
        pump_status_history.append(num_pumps_on)

        # 运行一个步长
        host.step(dt=1.0)

    # 5. 绘图
    results_df = host.get_datalogger().get_as_dataframe()
    results_df['pump_status'] = pump_status_history

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    fig.suptitle('第七章: 水泵启停控制仿真', fontsize=16)

    # 图1：水位变化
    ax1.plot(results_df.index, results_df['Sump.value'], label='低位集水池水位')
    ax1.axhline(y=3.0, color='r', linestyle='--', label='开泵水位 (3m)')
    ax1.axhline(y=1.0, color='g', linestyle='--', label='关泵水位 (1m)')
    ax1.set_ylabel('水位 (m)')
    ax1.legend()
    ax1.grid(True)

    ax1b = ax1.twinx()
    ax1b.plot(results_df.index, results_df['Reservoir.value'], 'k:', label='高位水库水位')
    ax1b.set_ylabel('高位水库水位 (m)')
    ax1b.legend(loc='upper right')

    # 图2：水泵状态和流量
    ax2.plot(results_df.index, results_df['pump_status'], 'm-', drawstyle='steps-post', label='水泵状态 (On/Off)')
    ax2.set_ylabel('水泵状态')
    ax2.set_xlabel('时间 (秒)')
    ax2.legend(loc='upper left')

    ax2b = ax2.twinx()
    ax2b.plot(results_df.index, results_df['PumpStation.value'], 'c:', label='泵站流量')
    ax2b.set_ylabel('流量 (m³/s)')
    ax2b.legend(loc='upper right')
    ax2b.grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

if __name__ == "__main__":
    run_simulation()
