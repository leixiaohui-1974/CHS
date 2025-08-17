import matplotlib.pyplot as plt
from chs_sdk.core.host import Host
from chs_sdk.modules.modeling.storage_models import FirstOrderStorageModel
from chs_sdk.modules.control.pid_controller import PIDController
from chs_sdk.modules.modeling.control_structure_models import GateStationModel
from chs_sdk.modules.modeling.instrument_models import GateActuator, LevelSensor

def run_simulation():
    """
    This script demonstrates a more realistic control loop involving a sensor,
    a PID controller, an actuator, and a physical gate model to control
    the level of a reservoir.
    """
    host = Host()

    # 1. 创建组件
    reservoir_agent = FirstOrderStorageModel(name='MyReservoir', initial_value=5.0, time_constant=1000.0) # 慢响应水库
    level_sensor = LevelSensor(name='ReservoirSensor', noise_std_dev=0.1)
    gate_actuator = GateActuator(name='InflowGateActuator', travel_time=120.0)
    inflow_gate = GateStationModel(name='InflowGate', num_gates=2, gate_width=2.0, discharge_coeff=0.8)
    pid_agent = PIDController(name='GatePID', setpoint=10.0, kp=0.8, ki=0.05, kd=0.2, output_min=0.0, output_max=1.0)

    # 2. 添加到主机
    host.add_agent(reservoir_agent)
    host.add_agent(level_sensor)
    host.add_agent(gate_actuator)
    host.add_agent(inflow_gate)
    host.add_agent(pid_agent)

    # 3. 连接因果链
    host.add_connection('MyReservoir', 'value', 'ReservoirSensor', 'true_value')
    host.add_connection('ReservoirSensor', 'value', 'GatePID', 'measured_value')
    host.add_connection('GatePID', 'output', 'InflowGateActuator', 'command')
    host.add_connection('InflowGateActuator', 'value', 'InflowGate', 'gate_opening')
    inflow_gate.set_input('upstream_level', 15.0)
    inflow_gate.set_input('downstream_level', reservoir_agent.get_port('value')) # 闸门出流受下游水位影响
    host.add_connection('InflowGate', 'value', 'MyReservoir', 'inflow')

    # 4. 运行
    host.run(num_steps=1000, dt=1.0)

    # 5. 绘图
    results_df = host.get_datalogger().get_as_dataframe()
    print("仿真结果 (前5行):")
    print(results_df.head())

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)

    ax1.plot(results_df.index, results_df['MyReservoir.value'], 'b-', linewidth=2, label='真实水位')
    ax1.plot(results_df.index, results_df['ReservoirSensor.value'], 'k.', markersize=2, alpha=0.5, label='传感器水位')
    ax1.axhline(y=10.0, color='r', linestyle='--', label='设定值')
    ax1.set_ylabel('水位 (m)')
    ax1.set_title('第六章: 带执行器和传感器的闸门控制仿真')
    ax1.legend()
    ax1.grid(True)

    ax2.plot(results_df.index, results_df['GatePID.output'], 'g--', label='PID 指令 (目标开度)')
    ax2.plot(results_df.index, results_df['InflowGateActuator.value'], 'm-', linewidth=2, label='执行器实际开度')
    ax2.set_ylabel('闸门开度 (0-1)')
    ax2.set_xlabel('时间 (秒)')
    ax2.legend(loc='upper left')
    ax2.grid(True)

    ax2b = ax2.twinx()
    ax2b.plot(results_df.index, results_df['InflowGate.value'], 'c:', label='闸门流量')
    ax2b.set_ylabel('流量 (m³/s)')
    ax2b.legend(loc='upper right')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_simulation()
