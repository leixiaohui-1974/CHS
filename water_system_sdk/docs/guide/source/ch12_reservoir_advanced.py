import matplotlib.pyplot as plt
import numpy as np
from chs_sdk.core.host import Host
from chs_sdk.modules.modeling.storage_models import NonlinearTank
from chs_sdk.modules.disturbances.predefined import TimeSeriesDisturbance

def run_simulation():
    """
    This script demonstrates how to use the NonlinearTank model to simulate
    a reservoir with an irregular shape, defined by a level-volume curve.
    """
    host = Host()

    # 1. 定义水位-库容曲线
    # 这是一个 2xN 的NumPy数组
    # 第0行: 水位 (m)
    # 第1行: 对应的库容 (m³)
    level_volume_curve = np.array([
        [10.0, 11.0,  12.0,  13.0,   14.0,   15.0],      # 水位
        [0.0,  1e5, 2.5e5, 4.5e5, 7.0e5, 10.0e5]   # 库容
    ])

    # 2. 创建组件
    # 使用曲线初始化非线性水库，初始水位为11.5米
    reservoir = NonlinearTank(
        name='IrregularReservoir',
        level_to_volume=level_volume_curve,
        initial_level=11.5
    )

    # 创建一个随时间变化的入流过程
    inflow_times = [0, 12, 24, 36, 48] # 小时
    inflow_values = [5, 50, 20, 10, 5] # m³/s
    inflow_disturbance = TimeSeriesDisturbance(
        name='FloodInflow',
        times=inflow_times,
        values=inflow_values
    )

    # 假设一个恒定的出流
    outflow_disturbance = TimeSeriesDisturbance(name='BaseOutflow', values=[-2.0]) # 恒定出流2m³/s

    # 3. 添加到主机
    host.add_agent(reservoir)
    host.add_agent(inflow_disturbance)
    host.add_agent(outflow_disturbance)

    # 4. 连接
    host.add_connection('FloodInflow', 'value', 'IrregularReservoir', 'inflow')
    host.add_connection('BaseOutflow', 'value', 'IrregularReservoir', 'release_outflow')

    # 5. 运行仿真
    # 注意：TimeSeriesDisturbance 使用秒作为时间单位
    host.run(num_steps=48*60, dt=60.0) # 模拟48小时，每分钟一步

    # 6. 绘图
    results_df = host.get_datalogger().get_as_dataframe()
    print("仿真结果 (前5行):")
    print(results_df.head())

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    fig.suptitle('第十二章: 非线性水库洪水演算', fontsize=16)

    # 图1：水位
    ax1.plot(results_df.index / 3600, results_df['IrregularReservoir.level'], 'b-', label='水库水位')
    ax1.set_ylabel('水位 (m)')
    ax1.legend()
    ax1.grid(True)

    # 图2：流量
    ax2.plot(results_df.index / 3600, results_df['FloodInflow.value'], 'c-', label='入库流量')
    ax2.set_ylabel('流量 (m³/s)')
    ax2.set_xlabel('时间 (小时)')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

if __name__ == "__main__":
    run_simulation()
