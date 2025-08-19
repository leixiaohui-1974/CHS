import matplotlib.pyplot as plt
import pandas as pd

from chs_sdk.core.host import AgentKernel as Host
from chs_sdk.modules.modeling.storage_models import FirstOrderInertiaModel
from chs_sdk.modules.disturbances.timeseries_disturbance import TimeSeriesDisturbance
from project_utils import EulerMethod, ModelAgent

def run_simulation():
    """
    This script simulates the peak shaving effect of a stormwater detention pond
    on a runoff hydrograph.
    """
    host = Host()

    # 1. 定义入流洪水波
    inflow_times = [0, 1*3600, 2*3600]  # 秒
    inflow_values = [0, 5.0, 0]        # m³/s
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='RunoffInflow',
        model_class=TimeSeriesDisturbance,
        times=inflow_times,
        values=inflow_values
    )

    # 2. 创建调蓄池模型
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='DetentionPond',
        model_class=FirstOrderInertiaModel,
        initial_storage=0.0,
        time_constant=3*3600,
        solver_class=EulerMethod,
        dt=60.0
    )

    # 3. 建立连接
    inflow_agent = host._agents['RunoffInflow']
    pond_agent = host._agents['DetentionPond']
    pond_agent.subscribe(f"{inflow_agent.agent_id}/output", 'inflow')

    # 4. 运行仿真
    num_steps = 6 * 60
    dt = 60.0
    results = []
    host.start(time_step=dt)
    for i in range(num_steps):
        host.tick()
        results.append({
            'time': host.current_time,
            'RunoffInflow.value': inflow_agent.model.output,
            'DetentionPond.outflow': pond_agent.model.output
        })

    # 5. 绘图
    results_df = pd.DataFrame(results)
    print("仿真结果 (前5行):")
    print(results_df.head())

    plt.figure(figsize=(12, 7))
    plt.title('第十三章: 雨水调蓄池削峰作用仿真', fontsize=16)

    plt.plot(results_df['time'] / 3600, results_df['RunoffInflow.value'], 'b-', label='入池流量 (径流)')
    plt.plot(results_df['time'] / 3600, results_df['DetentionPond.outflow'], 'r--', label='出池流量 (削峰后)')

    plt.xlabel('时间 (小时)')
    plt.ylabel('流量 (m³/s)')
    plt.legend()
    plt.grid(True)

    # 标注洪峰流量
    inflow_peak = results_df['RunoffInflow.value'].max()
    outflow_peak = results_df['DetentionPond.outflow'].max()
    plt.text(1.1, inflow_peak, f'入流洪峰: {inflow_peak:.2f} m³/s')
    plt.text(2.5, outflow_peak, f'出流洪峰: {outflow_peak:.2f} m³/s')

    plt.show()

if __name__ == "__main__":
    run_simulation()
