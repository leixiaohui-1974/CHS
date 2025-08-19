import matplotlib.pyplot as plt

from chs_sdk.core.host import AgentKernel as Host
from chs_sdk.modules.modeling.storage_models import FirstOrderInertiaModel
from chs_sdk.modules.disturbances.predefined import Disturbance
from water_system_sdk.docs.guide.source.project_utils import EulerMethod, ModelAgent
import pandas as pd

def run_simulation():
    """
    This script demonstrates the basic setup and execution of a simulation
    for a single reservoir with a constant inflow.
    """
    # 1. 创建一个仿真主机
    host = Host()

    # 2. 定义并注册水库模型智能体
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='MyReservoir',
        model_class=FirstOrderInertiaModel,
        initial_storage=10.0,
        time_constant=5.0,
        solver_class=EulerMethod,
        dt=1.0
    )

    # 3. 定义并注册一个恒定入流扰动智能体
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='inflow',
        model_class=Disturbance,
        signal_type='constant',
        value=5.0
    )

    # 4. 建立连接
    reservoir_agent = host._agents['MyReservoir']
    inflow_agent = host._agents['inflow']
    reservoir_agent.subscribe(topic=f"{inflow_agent.agent_id}/output", port_name='inflow')

    # 5. 运行仿真
    num_steps = 24
    dt = 1.0
    results = []
    host.start(time_step=dt)
    for i in range(num_steps):
        host.tick()
        results.append({
            'time': host.current_time,
            'reservoir_storage': reservoir_agent.model.state.storage,
            'reservoir_outflow': reservoir_agent.model.state.output
        })


    # 6. 可视化结果
    results_df = pd.DataFrame(results)
    print("仿真结果:")
    print(results_df)

    plt.figure(figsize=(10, 6))
    plt.plot(results_df['time'], results_df['reservoir_storage'], label='水库蓄水量')
    plt.xlabel('时间 (小时)')
    plt.ylabel('蓄水量 (单位)')
    plt.title('水库仿真结果')
    plt.grid(True)
    plt.legend()
    plt.show()

if __name__ == "__main__":
    run_simulation()
