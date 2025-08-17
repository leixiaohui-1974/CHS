import matplotlib.pyplot as plt

from chs_sdk.core.host import Host
from chs_sdk.modules.modeling.storage_models import FirstOrderStorageModel
from chs_sdk.modules.disturbances.predefined import ConstantDisturbance

def run_simulation():
    """
    This script demonstrates the basic setup and execution of a simulation
    for a single reservoir with a constant inflow.
    """
    # 1. 创建一个仿真主机
    host = Host()

    # 2. 定义水库模型智能体
    reservoir_agent = FirstOrderStorageModel(
        name='MyReservoir',
        initial_value=10.0,
        time_constant=5.0
    )

    # 3. 定义一个恒定入流扰动智能体
    inflow_agent = ConstantDisturbance(
        name='inflow',
        constant_value=5.0
    )

    # 4. 注册组件和连接
    host.add_agent(reservoir_agent)
    host.add_agent(inflow_agent)
    host.add_connection(
        source_agent_name='inflow',
        target_agent_name='MyReservoir',
        source_port_name='value',
        target_port_name='inflow'
    )

    # 5. 运行仿真
    host.run(num_steps=24, dt=1.0)

    # 6. 可视化结果
    results_df = host.get_datalogger().get_as_dataframe()
    print("仿真结果:")
    print(results_df)

    plt.figure(figsize=(10, 6))
    plt.plot(results_df.index, results_df['MyReservoir.value'], label='水库蓄水量')
    plt.xlabel('时间 (小时)')
    plt.ylabel('蓄水量 (单位)')
    plt.title('水库仿真结果')
    plt.grid(True)
    plt.legend()
    plt.show()

if __name__ == "__main__":
    run_simulation()
