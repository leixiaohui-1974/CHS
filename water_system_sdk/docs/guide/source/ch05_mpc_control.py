import matplotlib.pyplot as plt

from chs_sdk.core.host import Host
from chs_sdk.modules.modeling.storage_models import FirstOrderStorageModel
from chs_sdk.modules.control.mpc_controller import MPCController

def run_simulation():
    """
    This script demonstrates how to use a Model Predictive Control (MPC)
    controller to manage the water level of a reservoir.
    """
    # 1. 创建一个仿真主机
    host = Host()

    # 2. 定义“真实”的水库模型智能体
    reservoir_agent = FirstOrderStorageModel(
        name='MyReservoir',
        initial_value=10.0,
        time_constant=5.0
    )

    # 3. 创建MPC控制器
    # 3.1 MPC需要一个内部预测模型
    prediction_model_for_mpc = FirstOrderStorageModel(
        name='InternalPredictionModel',
        initial_value=10.0,
        time_constant=5.0
    )
    # 3.2 创建MPC控制器智能体
    mpc_agent = MPCController(
        name='MyMPCController',
        prediction_model=prediction_model_for_mpc,
        prediction_horizon=10,
        control_horizon=3,
        set_point=15.0,
        q_weight=1.0,
        r_weight=0.1,
        u_min=0.0,
        u_max=20.0
    )

    # 4. 注册智能体和连接
    host.add_agent(reservoir_agent)
    host.add_agent(mpc_agent)

    # 连接水库水位到MPC输入
    host.add_connection(
        source_agent_name='MyReservoir',
        target_agent_name='MyMPCController',
        source_port_name='value',
        target_port_name='current_state'
    )

    # 连接MPC输出到水库入流
    host.add_connection(
        source_agent_name='MyMPCController',
        target_agent_name='MyReservoir',
        source_port_name='output',
        target_port_name='inflow'
    )

    # 5. 运行仿真
    host.run(num_steps=50, dt=1.0)

    # 6. 可视化结果
    results_df = host.get_datalogger().get_as_dataframe()
    print("仿真结果:")
    print(results_df.head())

    plt.figure(figsize=(12, 8))

    plt.subplot(2, 1, 1)
    plt.plot(results_df.index, results_df['MyReservoir.value'], label='水库蓄水量')
    plt.axhline(y=15.0, color='r', linestyle='--', label='设定值 (15.0)')
    plt.title('水库蓄水水位 (MPC控制)')
    plt.ylabel('蓄水量 (单位)')
    plt.legend()
    plt.grid(True)

    plt.subplot(2, 1, 2)
    plt.plot(results_df.index, results_df['MyMPCController.output'], label='MPC 输出 (入流量)')
    plt.title('控制器输出')
    plt.ylabel('流量 (单位)')
    plt.xlabel('时间 (小时)')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_simulation()
