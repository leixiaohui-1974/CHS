import matplotlib.pyplot as plt
import pandas as pd

from chs_sdk.core.host import AgentKernel as Host
from chs_sdk.modules.modeling.storage_models import FirstOrderInertiaModel
from chs_sdk.modules.control.mpc_controller import MPCController
from water_system_sdk.docs.guide.source.project_utils import EulerMethod, ModelAgent

def run_simulation():
    """
    This script demonstrates how to use a Model Predictive Control (MPC)
    controller to manage the water level of a reservoir.
    """
    # 1. 创建一个仿真主机
    host = Host()

    # 2. 定义“真实”的水库模型智能体
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='MyReservoir',
        model_class=FirstOrderInertiaModel,
        initial_storage=10.0,
        time_constant=5.0,
        solver_class=EulerMethod,
        dt=1.0
    )

    # 3. 创建MPC控制器
    # 3.1 MPC需要一个内部预测模型
    prediction_model_for_mpc = FirstOrderInertiaModel(
        initial_storage=10.0,
        time_constant=5.0,
        solver_class=EulerMethod,
        dt=1.0
    )
    # 3.2 创建并注册MPC控制器智能体
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='MyMPCController',
        model_class=MPCController,
        prediction_model=prediction_model_for_mpc,
        prediction_horizon=10,
        control_horizon=3,
        set_point=15.0,
        q_weight=1.0,
        r_weight=0.1,
        u_min=0.0,
        u_max=20.0
    )

    # 4. 建立连接
    reservoir_agent = host._agents['MyReservoir']
    mpc_agent = host._agents['MyMPCController']

    # 连接水库水位到MPC输入
    mpc_agent.subscribe(topic=f"{reservoir_agent.agent_id}/output", port_name='current_state')

    # 连接MPC输出到水库入流
    reservoir_agent.subscribe(topic=f"{mpc_agent.agent_id}/output", port_name='inflow')

    # 5. 运行仿真
    num_steps = 50
    dt = 1.0
    results = []
    host.start(time_step=dt)
    for i in range(num_steps):
        host.tick()
        results.append({
            'time': host.current_time,
            'reservoir_storage': reservoir_agent.model.state.storage,
            'mpc_output': mpc_agent.model.current_control_action
        })

    # 6. 可视化结果
    results_df = pd.DataFrame(results)
    print("仿真结果:")
    print(results_df.head())

    plt.figure(figsize=(12, 8))

    plt.subplot(2, 1, 1)
    plt.plot(results_df['time'], results_df['reservoir_storage'], label='水库蓄水量')
    plt.axhline(y=15.0, color='r', linestyle='--', label='设定值 (15.0)')
    plt.title('水库蓄水水位 (MPC控制)')
    plt.ylabel('蓄水量 (单位)')
    plt.legend()
    plt.grid(True)

    plt.subplot(2, 1, 2)
    plt.plot(results_df['time'], results_df['mpc_output'], label='MPC 输出 (入流量)')
    plt.title('控制器输出')
    plt.ylabel('流量 (单位)')
    plt.xlabel('时间 (小时)')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_simulation()
