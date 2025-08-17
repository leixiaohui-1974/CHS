import matplotlib.pyplot as plt

from chs_sdk.core.host import Host
from chs_sdk.modules.modeling.storage_models import FirstOrderStorageModel
from chs_sdk.modules.control.pid_controller import PIDController

def run_simulation():
    """
    This script demonstrates how to use a PID controller to manage the
    water level of a reservoir.
    """
    # 1. 创建一个仿真主机
    host = Host()

    # 2. 定义水库模型智能体
    reservoir_agent = FirstOrderStorageModel(
        name='MyReservoir',
        initial_value=10.0,
        time_constant=5.0
    )

    # 3. 创建PID控制器智能体
    pid_agent = PIDController(
        name='MyPIDController',
        kp=1.5,
        ki=0.1,
        kd=0.5,
        setpoint=15.0
    )

    # 4. 注册智能体和连接
    host.add_agent(reservoir_agent)
    host.add_agent(pid_agent)

    # 将水库水位连接到PID输入
    host.add_connection(
        source_agent_name='MyReservoir',
        target_agent_name='MyPIDController',
        source_port_name='value',
        target_port_name='measured_value'
    )

    # 将PID输出连接到水库入流
    host.add_connection(
        source_agent_name='MyPIDController',
        target_agent_name='MyReservoir',
        source_port_name='output',
        target_port_name='inflow'
    )

    # 5. 运行仿真
    host.run(num_steps=50, dt=1.0) # 运行更长时间以观察其稳定过程

    # 6. 可视化结果
    results_df = host.get_datalogger().get_as_dataframe()
    print("仿真结果:")
    print(results_df.head())

    plt.figure(figsize=(12, 8))

    plt.subplot(2, 1, 1)
    plt.plot(results_df.index, results_df['MyReservoir.value'], label='水库蓄水量')
    plt.axhline(y=15.0, color='r', linestyle='--', label='设定值 (15.0)')
    plt.title('水库蓄水水位 (PID 控制)')
    plt.ylabel('蓄水量 (单位)')
    plt.legend()
    plt.grid(True)

    plt.subplot(2, 1, 2)
    plt.plot(results_df.index, results_df['MyPIDController.output'], label='PID 输出 (入流量)')
    plt.title('控制器输出')
    plt.ylabel('流量 (单位)')
    plt.xlabel('时间 (小时)')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_simulation()
