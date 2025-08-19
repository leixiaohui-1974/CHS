import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
import numpy as np
import pandas as pd

from chs_sdk.core.host import AgentKernel as Host
from chs_sdk.modules.modeling.storage_models import NonlinearTank
from chs_sdk.modules.disturbances.timeseries_disturbance import TimeSeriesDisturbance
from water_system_sdk.docs.guide.source.project_utils import ModelAgent

def run_simulation():
    """
    This script demonstrates how to use the NonlinearTank model to simulate
    a reservoir with an irregular shape, defined by a level-volume curve.
    """
    host = Host()

    # 1. 定义水位-库容曲线
    level_volume_curve = np.array([
        [10.0, 11.0,  12.0,  13.0,   14.0,   15.0],      # 水位
        [0.0,  1e5, 2.5e5, 4.5e5, 7.0e5, 10.0e5]   # 库容
    ])

    # 2. 创建组件
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='IrregularReservoir',
        model_class=NonlinearTank,
        level_to_volume=level_volume_curve,
        initial_level=11.5)

    inflow_times_hours = [0, 12, 24, 36, 48]
    inflow_times_seconds = [t * 3600 for t in inflow_times_hours]
    inflow_values = [5, 50, 20, 10, 5]
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='FloodInflow',
        model_class=TimeSeriesDisturbance,
        times=inflow_times_seconds,
        values=inflow_values)

    host.add_agent(
        agent_class=ModelAgent,
        agent_id='BaseOutflow',
        model_class=TimeSeriesDisturbance,
        times=[0],
        values=[-2.0])

    # 3. 建立连接
    reservoir_agent = host._agents['IrregularReservoir']
    inflow_agent = host._agents['FloodInflow']
    outflow_agent = host._agents['BaseOutflow']

    reservoir_agent.subscribe(f"{inflow_agent.agent_id}/output", 'inflow')
    reservoir_agent.subscribe(f"{outflow_agent.agent_id}/output", 'release_outflow')

    # 4. 运行仿真
    num_steps = 48 * 60
    dt = 60.0
    results = []
    host.start(time_step=dt)
    for i in range(num_steps):
        host.tick()
        results.append({
            'time': host.current_time,
            'IrregularReservoir.level': reservoir_agent.model.level,
            'FloodInflow.value': inflow_agent.model.output
        })

    # 5. 绘图
    results_df = pd.DataFrame(results)
    print("仿真结果 (前5行):")
    print(results_df.head())

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    fig.suptitle('第十二章: 非线性水库洪水演算', fontsize=16)

    # 图1：水位
    ax1.plot(results_df['time'] / 3600, results_df['IrregularReservoir.level'], 'b-', label='水库水位')
    ax1.set_ylabel('水位 (m)')
    ax1.legend()
    ax1.grid(True)

    # 图2：流量
    ax2.plot(results_df['time'] / 3600, results_df['FloodInflow.value'], 'c-', label='入库流量')
    ax2.set_ylabel('流量 (m^3/s)')
    ax2.set_xlabel('时间 (小时)')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

if __name__ == "__main__":
    run_simulation()
