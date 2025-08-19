import matplotlib.pyplot as plt
import pandas as pd

from chs_sdk.core.host import AgentKernel as Host
from chs_sdk.modules.modeling.storage_models import LinearTank
from chs_sdk.modules.control.pid_controller import PIDController
from chs_sdk.modules.modeling.valve_models import ButterflyValve
from water_system_sdk.docs.guide.source.project_utils import ModelAgent

def run_simulation():
    """
    This script demonstrates how to use a PID controller to modulate a
    valve's opening to achieve a target flow rate in a pressurized pipe system.
    """
    host = Host()

    # 1. 创建组件
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='DownstreamReservoir',
        model_class=LinearTank,
        initial_level=10.0,
        area=500)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='ControlValve',
        model_class=ButterflyValve,
        cv_max=10.0,
        slew_rate=1.0/60.0)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='FlowPID',
        model_class=PIDController,
        set_point=2.5,
        Kp=0.5,
        Ki=0.2,
        Kd=0.1,
        output_min=0.0,
        output_max=1.0)

    # 2. 建立连接
    downstream_reservoir_agent = host._agents['DownstreamReservoir']
    valve_agent = host._agents['ControlValve']
    pid_agent = host._agents['FlowPID']

    pid_agent.subscribe(f"{valve_agent.agent_id}/output", 'error_source')
    valve_agent.subscribe(f"{pid_agent.agent_id}/output", 'command')
    downstream_reservoir_agent.subscribe(f"{valve_agent.agent_id}/output", 'inflow')

    # 3. 运行与手动设置边界条件
    num_steps = 600
    dt = 1.0
    results = []
    host.start(time_step=dt)
    for i in range(num_steps):
        # 在每一步手动设置阀门的上下游压力（用水位代替）
        valve_agent.input_values['upstream_pressure'] = 50.0
        valve_agent.input_values['downstream_pressure'] = downstream_reservoir_agent.model.output

        host.tick()

        results.append({
            'time': host.current_time,
            'ControlValve.value': valve_agent.model.output,
            'FlowPID.output': pid_agent.model.output,
            'ControlValve.actual_position': valve_agent.model.get_current_position()
        })

    # 4. 绘图
    results_df = pd.DataFrame(results)
    print("仿真结果 (前5行):")
    print(results_df.head())

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    fig.suptitle('第八章: PID阀门流量控制仿真', fontsize=16)

    # 图1：流量控制
    ax1.plot(results_df['time'], results_df['ControlValve.value'], 'b-', label='实际流量')
    ax1.axhline(y=2.5, color='r', linestyle='--', label='目标流量 (2.5 m³/s)')
    ax1.set_ylabel('流量 (m³/s)')
    ax1.legend()
    ax1.grid(True)

    # 图2：阀门开度
    ax2.plot(results_df['time'], results_df['FlowPID.output'], 'g--', label='PID指令 (目标开度)')
    ax2.plot(results_df['time'], results_df['ControlValve.actual_position'], 'm-', label='阀门实际开度')
    ax2.set_xlabel('时间 (秒)')
    ax2.set_ylabel('阀门开度 (0-1)')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

if __name__ == "__main__":
    run_simulation()
