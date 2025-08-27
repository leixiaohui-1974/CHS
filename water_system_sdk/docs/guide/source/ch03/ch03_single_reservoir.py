import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

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
        reservoir_area=100.0,  # 添加水库面积100 m²
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
            'reservoir_water_level': reservoir_agent.model.state.storage / 100.0,  # 计算水位 = 蓄水量/面积
            'reservoir_outflow': reservoir_agent.model.state.output
        })


    # 6. 可视化结果
    results_df = pd.DataFrame(results)
    print("仿真结果:")
    print(results_df)
    print(f"\n初始水位: {results_df['reservoir_water_level'].iloc[0]:.3f} m")
    print(f"最终水位: {results_df['reservoir_water_level'].iloc[-1]:.3f} m")
    print(f"水位变化: {results_df['reservoir_water_level'].iloc[-1] - results_df['reservoir_water_level'].iloc[0]:.3f} m")

    # 创建两个子图
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # 上图：水位
    ax1.plot(results_df['time'], results_df['reservoir_water_level'], 'b-', linewidth=2, label='水库水位')
    ax1.set_ylabel('水位 (m)')
    ax1.set_title('水库水位变化')
    ax1.legend()
    ax1.grid(True)
    
    # 下图：蓄水量
    ax2.plot(results_df['time'], results_df['reservoir_storage'], 'g-', linewidth=2, label='水库蓄水量')
    ax2.set_xlabel('时间 (h)')
    ax2.set_ylabel('蓄水量 (m^3)')
    ax2.set_title('水库蓄水量变化')
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_simulation()
