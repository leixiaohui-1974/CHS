import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
import pandas as pd

from chs_sdk.core.host import AgentKernel as Host
from chs_sdk.modules.modeling.storage_models import FirstOrderInertiaModel
from chs_sdk.modules.control.pid_controller import PIDController
from chs_sdk.modules.modeling.control_structure_models import SluiceGate
from water_system_sdk.docs.guide.source.project_utils import EulerMethod, ModelAgent, LevelSensor

def run_simulation():
    """
    This script demonstrates a more realistic control loop involving a sensor,
    a PID controller, an actuator, and a physical gate model to control
    the level of a reservoir.
    """
    host = Host()

    # 1. 创建组件
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='MyReservoir',
        model_class=FirstOrderInertiaModel,
        initial_storage=5.0,
        time_constant=1000.0,
        solver_class=EulerMethod,
        dt=1.0)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='ReservoirSensor',
        model_class=LevelSensor,
        noise_stddev=0.1)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='InflowGate',
        model_class=SluiceGate,
        gate_width=2.0,
        discharge_coeff=0.8,
        slew_rate=1.0/120.0,
        initial_opening=0.0)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='GatePID',
        model_class=PIDController,
        set_point=10.0,
        Kp=0.8,
        Ki=0.05,
        Kd=0.2,
        output_min=0.0,
        output_max=1.0)

    # 2. 建立连接
    reservoir_agent = host._agents['MyReservoir']
    level_sensor = host._agents['ReservoirSensor']
    inflow_gate = host._agents['InflowGate']
    pid_agent = host._agents['GatePID']

    level_sensor.subscribe(f"{reservoir_agent.agent_id}/output", 'true_value')
    pid_agent.subscribe(f"{level_sensor.agent_id}/output", 'error_source')
    inflow_gate.subscribe(f"{pid_agent.agent_id}/output", 'command')
    inflow_gate.subscribe(f"{reservoir_agent.agent_id}/output", 'downstream_level')
    inflow_gate.input_values['upstream_level'] = 15.0 # Set constant input
    reservoir_agent.subscribe(f"{inflow_gate.agent_id}/output", 'inflow')


    # 3. 运行
    num_steps = 1000
    dt = 1.0
    results = []
    host.start(time_step=dt)
    for i in range(num_steps):
        host.tick()
        results.append({
            'time': host.current_time,
            'MyReservoir.value': reservoir_agent.model.state.storage,
            'ReservoirSensor.value': level_sensor.model.output,
            'GatePID.output': pid_agent.model.output,
            'InflowGateActuator.value': inflow_gate.model.get_current_position(),
            'InflowGate.value': inflow_gate.model.output,
        })

    # 4. 绘图
    results_df = pd.DataFrame(results)
    print("仿真结果 (前5行):")
    print(results_df.head())

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)

    ax1.plot(results_df['time'], results_df['MyReservoir.value'], 'b-', linewidth=2, label='真实水位')
    ax1.plot(results_df['time'], results_df['ReservoirSensor.value'], 'k.', markersize=2, alpha=0.5, label='传感器水位')
    ax1.axhline(y=10.0, color='r', linestyle='--', label='设定值')
    ax1.set_ylabel('水位 (m)')
    ax1.set_title('第六章: 带执行器和传感器的闸门控制仿真')
    ax1.legend()
    ax1.grid(True)

    ax2.plot(results_df['time'], results_df['GatePID.output'], 'g--', label='PID 指令 (目标开度)')
    ax2.plot(results_df['time'], results_df['InflowGateActuator.value'], 'm-', linewidth=2, label='执行器实际开度')
    ax2.set_ylabel('闸门开度 (0-1)')
    ax2.set_xlabel('时间 (秒)')
    ax2.legend(loc='upper left')
    ax2.grid(True)

    ax2b = ax2.twinx()
    ax2b.plot(results_df['time'], results_df['InflowGate.value'], 'c:', label='闸门流量')
    ax2b.set_ylabel('流量 (m^3/s)')
    ax2b.legend(loc='upper right')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_simulation()
