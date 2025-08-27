import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
import pandas as pd

from chs_sdk.core.host import AgentKernel as Host
from chs_sdk.modules.modeling.storage_models import FirstOrderInertiaModel
from chs_sdk.modules.control.pid_controller import PIDController
from chs_sdk.modules.modeling.control_structure_models import SluiceGate

class SmartInflowGate(SluiceGate):
    """
    智能入流闸门，PID直接输出闸门开度，执行器直接使用
    """
    def __init__(self, max_opening=4.0, **kwargs):
        super().__init__(**kwargs)
        self.max_opening = max_opening
    
    def step(self, upstream_level: float, downstream_level: float = 0.0, dt: float = 1.0, command: float = None, **kwargs):
        """
        PID直接输出物理开度，执行器直接使用
        PID输出范围：0到4米（物理开度）
        闸门开度范围：0到max_opening米（物理开度）
        """
        if command is not None:
            # PID输出直接作为物理开度，无需映射
            # command = 0.0 → 开度 = 0米（完全关闭）
            # command = 2.0 → 开度 = 2米（半开）
            # command = 4.0 → 开度 = 4米（完全打开）
            physical_opening = max(0.0, min(self.max_opening, command))
            self.set_target(physical_opening)
        
        # 调用父类的step方法
        return super().step(upstream_level, downstream_level, dt, **kwargs)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from project_utils import EulerMethod, ReservoirModelAgent, ModelAgent, LevelSensor

def run_simulation():
    """
    This script demonstrates a more realistic control loop involving a sensor,
    a PID controller, an actuator, and a physical gate model to control
    the level of a reservoir.
    """
    host = Host()

    # 1. 创建组件
    host.add_agent(
        agent_class=ReservoirModelAgent,  # 使用新的ReservoirModelAgent
        agent_id='MyReservoir',
        model_class=FirstOrderInertiaModel,
        initial_storage=5.0,
        time_constant=10.0,  # 减少时间常数，使出流更合理
        reservoir_area=1000.0,  # 水库面积1000.0 m²
        solver_class=EulerMethod,
        dt=0.5)  # 水库模型时间步长也改为0.5秒
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='ReservoirSensor',
        model_class=LevelSensor,
        reservoir_area=1000.0,     # 水库面积，用于计算水位
        noise_stddev=0.001,     # 减少噪声到1mm
        bias=0.0005,            # 减少偏差到0.5mm
        drift=0.00001,          # 减少漂移到0.01mm/s
        lag=0.01)               # 减少滞后到0.01s
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='InflowGate',
        model_class=SmartInflowGate,
        gate_width=15.0,  # 闸门宽度15.0米
        max_opening=4.0,  # 最大开度4.0米
        discharge_coeff=0.8,  # 流量系数0.8
        slew_rate=1.0,  # 增加响应速度，每秒可以改变1.0的开度
        initial_opening=0.0)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='GatePID',
        model_class=PIDController,
        set_point=5.0,  # 目标水位5.0米
        Kp=0.2,  # 比例增益（降低，减少超调）
        Ki=0.05,  # 积分增益（降低，减少累积误差）
        Kd=0.15,  # 微分增益（增加，增强阻尼效果）
        output_min=0.1,   # 闸门开度最小值（完全关闭，0米）
        output_max=4.0)   # 闸门开度最大值（完全打开，4米）

    # 2. 建立连接
    reservoir_agent = host._agents['MyReservoir']
    level_sensor = host._agents['ReservoirSensor']
    inflow_gate = host._agents['InflowGate']
    pid_agent = host._agents['GatePID']

    level_sensor.subscribe(f"{reservoir_agent.agent_id}/true_value", 'true_value')
    pid_agent.subscribe(f"{level_sensor.agent_id}/output", 'error_source')
    inflow_gate.subscribe(f"{pid_agent.agent_id}/output", 'command')
    # 闸门的下游水位应该是固定的，不是水库的水位
    inflow_gate.input_values['upstream_level'] = 15.0  # 上游水位
    inflow_gate.input_values['downstream_level'] = 0.0  # 下游水位固定为0
    reservoir_agent.subscribe(f"{inflow_gate.agent_id}/inflow", 'inflow')
    
    # 确保PID控制器有正确的输入结构
    if not hasattr(pid_agent.model, 'input'):
        from chs_sdk.core.datastructures import Input
        pid_agent.model.input = Input(error_source=0.0, current_value_offset=0.0)
    
    # 确保水库模型有正确的输入结构
    if not hasattr(reservoir_agent.model, 'input'):
        from chs_sdk.core.datastructures import Input
        reservoir_agent.model.input = Input(inflow=0.0, control_inflow=0.0)
    
    # 手动设置所有代理状态为RUNNING（修复消息总线问题）
    from chs_sdk.agents.agent_status import AgentStatus
    for agent in host._agents.values():
        agent.status = AgentStatus.RUNNING
        print(f"手动设置 {agent.agent_id} 状态为 RUNNING")
    
    # 添加异常处理来调试代理执行错误
    import traceback
    def safe_execute(agent, current_time, time_step):
        try:
            agent.execute(current_time, time_step)
        except Exception as e:
            print(f"代理 {agent.agent_id} 执行出错: {e}")
            print(f"错误详情: {traceback.format_exc()}")
            agent.status = AgentStatus.FAULT


    # 添加调试信息
    print(f"PID输入数据： {pid_agent.input_values}")
    print(f"水库输入数据： {reservoir_agent.input_values}")
    print(f"传感器输入数据： {level_sensor.input_values}")
    print(f"闸门输入数据： {inflow_gate.input_values}")
    
    # 检查订阅情况
    print(f"\n消息总线订阅情况：")
    for topic, subscribers in host.message_bus._subscriptions.items():
        print(f"  主题 '{topic}': {[s.agent_id for s in subscribers]}")
    
    # 检查代理状态
    print(f"\n代理状态：")
    for agent_id, agent in host._agents.items():
        print(f"  {agent_id}: {agent.status}")
    
    # 检查初始状态
    print(f"\n初始模型状态：")
    print(f"  水库存储量: {reservoir_agent.model.state.storage}")
    print(f"  传感器输出: {level_sensor.model.output}")
    print(f"  PID输出: {pid_agent.model.output}")
    print(f"  PID积分项: {pid_agent.model.state.integral}")
    print(f"  PID误差: {pid_agent.model.set_point - level_sensor.model.output}")
    print(f"  闸门开度: {inflow_gate.model.get_current_position()}")
    print(f"  闸门流量: {inflow_gate.model.output}")
    
    # 3. 运行
    num_steps = 100  # 仿真时间50秒（100步 × 0.5秒）
    dt = 0.5  # 传感器数据采集频率改为0.5秒一次
    results = []
    host.start(time_step=dt)
    for i in range(num_steps):
        # 手动执行tick逻辑，使用安全的执行方法
        current_time = host.current_time
        
        # 1. 执行代理逻辑
        for agent in host._agents.values():
            if agent.status == AgentStatus.RUNNING:
                safe_execute(agent, current_time, dt)
        
        # 2. 分发消息
        host.message_bus.dispatch()
        
        # 3. 推进时间
        host.current_time += dt
        results.append({
            'time': host.current_time,
            'MyReservoir.value': reservoir_agent.model.state.storage / 1000.0,  # 转换为水位（面积=1000.0 m²）
            'ReservoirSensor.value': level_sensor.model.output,
            'GatePID.output': pid_agent.model.output,
            'InflowGateActuator.value': inflow_gate.model.get_current_position(),
            'InflowGate.value': inflow_gate.model.output,
        })
        
        # 每步后检查参数传递情况
        print(f"\n步骤 {i+1}:")
        print(f"  PID输入： {pid_agent.input_values}")
        print(f"  水库输入： {reservoir_agent.input_values}") 
        print(f"  PID状态： error_source={getattr(pid_agent.model.input, 'error_source', 'N/A')}")
        print(f"  PID误差： {pid_agent.model.set_point - getattr(pid_agent.model.input, 'error_source', 0)}")
        print(f"  PID积分项： {pid_agent.model.state.integral}")
        print(f"  PID输出： {pid_agent.model.output}")
        print(f"  水库状态： inflow={getattr(reservoir_agent.model.input, 'inflow', 'N/A')}")
        print(f"  消息队列长度： {host.message_bus.get_topic_queue_lengths()}")

    # 4. 绘图
    results_df = pd.DataFrame(results)
    print("仿真结果 (前5行):")
    print(results_df.head())

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)

    ax1.plot(results_df['time'], results_df['MyReservoir.value'], 'b-', linewidth=2, label='水库水位')
    ax1.plot(results_df['time'], results_df['ReservoirSensor.value'], 'k.', markersize=8, alpha=0.5, label='传感器水位')
    ax1.axhline(y=5.0, color='r', linestyle='--', label='目标水位')
    ax1.set_ylabel('水位 (m)')
    ax1.set_title('第六章: 带执行器和传感器的闸门控制仿真')
    ax1.legend()
    ax1.grid(True)

    ax2.plot(results_df['time'], results_df['GatePID.output'], 'g--', label='PID 指令')
    ax2.plot(results_df['time'], results_df['InflowGateActuator.value'], 'm-', linewidth=2, label='执行器实际开度')
    ax2.set_ylabel('闸门开度 (m)')
    ax2.set_xlabel('时间 (h)')
    ax2.legend(loc='upper left')
    ax2.grid(True)

    ax2b = ax2.twinx()
    ax2b.bar(results_df['time'], results_df['InflowGate.value'], alpha=0.6, color='cyan', width=0.3, label='过闸门流量')
    ax2b.set_ylabel('流量 (m^3/s)')
    ax2b.legend(loc='upper right')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_simulation()
