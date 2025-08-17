import matplotlib.pyplot as plt
from chs_sdk.core.host import Host
from chs_sdk.modules.modeling.storage_models import FirstOrderStorageModel
from chs_sdk.modules.control.pid_controller import PIDController
from chs_sdk.modules.modeling.valve_models import ButterflyValve

def run_simulation():
    """
    This script demonstrates how to use a PID controller to modulate a
    valve's opening to achieve a target flow rate in a pressurized pipe system.
    """
    host = Host()

    # 1. 创建组件
    # 假设上游水库水位恒定，我们只模拟下游水池
    downstream_reservoir = FirstOrderStorageModel(name='DownstreamReservoir', initial_value=10.0, area=500)

    # 创建一个蝶阀，最大Cv为10，完全开启/关闭需要60秒
    valve = ButterflyValve(name='ControlValve', cv_max=10.0, travel_time=60.0)

    # PID控制器用于控制流量
    pid = PIDController(name='FlowPID', setpoint=2.5, kp=0.5, ki=0.2, kd=0.1, output_min=0.0, output_max=1.0)

    # 2. 添加到主机
    host.add_agent(downstream_reservoir)
    host.add_agent(valve)
    host.add_agent(pid)

    # 3. 连接因果链
    # 3.1 PID的目标是控制阀门的流量
    host.add_connection('ControlValve', 'value', 'FlowPID', 'measured_value')
    # 3.2 PID的输出是阀门的目标开度
    host.add_connection('FlowPID', 'output', 'ControlValve', 'command')
    # 3.3 阀门的流量成为下游水池的入流
    host.add_connection('ControlValve', 'value', 'DownstreamReservoir', 'inflow')

    # 4. 运行与手动设置边界条件
    num_steps = 600
    for i in range(num_steps):
        # 在每一步手动设置阀门的上下游压力（用水位代替）
        # 这是因为在这个简化模型中，我们没有一个完整的管网来自动提供压力
        upstream_pressure = 50.0
        downstream_pressure = downstream_reservoir.get_port('value').value

        valve.set_input('upstream_pressure', upstream_pressure)
        valve.set_input('downstream_pressure', downstream_pressure)

        # 运行一个步长
        host.step(dt=1.0)

    # 5. 绘图
    results_df = host.get_datalogger().get_as_dataframe()
    print("仿真结果 (前5行):")
    print(results_df.head())

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    fig.suptitle('第八章: PID阀门流量控制仿真', fontsize=16)

    # 图1：流量控制
    ax1.plot(results_df.index, results_df['ControlValve.value'], 'b-', label='实际流量')
    ax1.axhline(y=2.5, color='r', linestyle='--', label='目标流量 (2.5 m³/s)')
    ax1.set_ylabel('流量 (m³/s)')
    ax1.legend()
    ax1.grid(True)

    # 图2：阀门开度
    ax2.plot(results_df.index, results_df['FlowPID.output'], 'g--', label='PID指令 (目标开度)')
    ax2.plot(results_df.index, results_df['ControlValve.actual_position'], 'm-', label='阀门实际开度')
    ax2.set_xlabel('时间 (秒)')
    ax2.set_ylabel('阀门开度 (0-1)')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

if __name__ == "__main__":
    run_simulation()
