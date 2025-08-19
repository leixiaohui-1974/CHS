import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
import pandas as pd

from chs_sdk.core.host import AgentKernel as Host
from chs_sdk.modules.modeling.storage_models import FirstOrderInertiaModel
from chs_sdk.modules.control.pid_controller import PIDController
from water_system_sdk.docs.guide.source.project_utils import EulerMethod, ModelAgent

def run_simulation():
    """
    This script demonstrates how to use a PID controller to manage the
    water level of a reservoir.
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

    # 3. 创建并注册PID控制器智能体
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='MyPIDController',
        model_class=PIDController,
        Kp=1.5,
        Ki=0.1,
        Kd=0.5,
        set_point=15.0
    )

    # 4. 建立连接
    reservoir_agent = host._agents['MyReservoir']
    pid_agent = host._agents['MyPIDController']

    # 将水库水位连接到PID输入
    pid_agent.subscribe(topic=f"{reservoir_agent.agent_id}/output", port_name='error_source')

    # 将PID输出连接到水库入流
    reservoir_agent.subscribe(topic=f"{pid_agent.agent_id}/output", port_name='inflow')


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
            'pid_output': pid_agent.model.output
        })

    # 6. 可视化结果
    results_df = pd.DataFrame(results)
    print("仿真结果:")
    print(results_df.head())

    plt.figure(figsize=(12, 8))

    plt.subplot(2, 1, 1)
    plt.plot(results_df['time'], results_df['reservoir_storage'], label='水库蓄水量')
    plt.axhline(y=15.0, color='r', linestyle='--', label='设定值 (15.0)')
    plt.title('水库蓄水水位 (PID 控制)')
    plt.ylabel('蓄水量 (单位)')
    plt.legend()
    plt.grid(True)

    plt.subplot(2, 1, 2)
    plt.plot(results_df['time'], results_df['pid_output'], label='PID 输出 (入流量)')
    plt.title('控制器输出')
    plt.ylabel('流量 (单位)')
    plt.xlabel('时间 (小时)')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_simulation()
