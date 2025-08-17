import matplotlib.pyplot as plt

# This is a simple way to make the SDK accessible to the script.
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from chs_sdk.core.host import Host
from chs_sdk.agents.base import BaseAgent
from chs_sdk.agents.message import Message
from chs_sdk.modules.modeling.storage_models import LinearTank
from chs_sdk.modules.modeling.control_structure_models import PumpStationModel
from chs_sdk.modules.disturbances.predefined import TimeSeriesDisturbance

# 1. 创建自定义的滞回控制器智能体
class HysteresisControllerAgent(BaseAgent):
    """
    A custom agent that implements hysteresis (on/off) control logic.
    It turns an actuator on when a measured value drops below a low
    threshold and turns it off when it rises above a high threshold.
    """
    def __init__(self, agent_id, kernel, **config):
        super().__init__(agent_id, kernel, **config)
        # 从config中读取参数
        self.low_threshold = config.get('low_threshold', 2.0)
        self.high_threshold = config.get('high_threshold', 4.0)
        self.input_topic = config.get('input_topic')
        self.output_topic = config.get('output_topic', f'cmd/{self.agent_id}/output')

        # 内部状态
        self.current_input = 0.0
        self.current_output = 0 # 初始为关闭状态 (0)

    def setup(self):
        # 订阅输入主题
        if self.input_topic:
            self.kernel.message_bus.subscribe(self, self.input_topic)
            print(f"[{self.agent_id}] 订阅了主题: {self.input_topic}")

    def on_message(self, message: Message):
        # 当收到新消息时，更新内部的当前输入值
        if message.topic == self.input_topic:
            # 假设 payload 是一个 {'value': ...} 的字典
            self.current_input = message.payload.get('value', 0.0)

    def execute(self, current_time: float, time_step: float):
        # 在每个时间步执行控制逻辑
        output_before = self.current_output
        if self.current_input < self.low_threshold:
            self.current_output = 1 # 低于下限，开启
        elif self.current_input > self.high_threshold:
            self.current_output = 0 # 高于上限，关闭
        # 如果在中间，则保持 self.current_output 不变

        if self.current_output != output_before:
            print(f"[{current_time:.0f}s] {self.agent_id}: Input is {self.current_input:.2f}, changing output to {self.current_output}")

        # 发布控制指令
        self._publish(self.output_topic, {"value": self.current_output})

def run_simulation_with_custom_agent():
    """
    This script demonstrates how to use the custom HysteresisControllerAgent
    to control a pump based on a tank's water level.
    """
    host = Host()

    # 2. 创建物理组件
    tank = LinearTank(name='MyTank', area=1000.0, initial_level=5.0)
    pump = PumpStationModel(name='MyPump', num_pumps_total=1, curve_coeffs=[-0.01, 0.1, 15])
    inflow = TimeSeriesDisturbance(name='Inflow', values=[0.2]) # 恒定入流

    # 3. 创建我们的自定义控制器实例
    # 它将监听 'state/tank/level' 主题，并向 'cmd/pump/on_off' 主题发布指令
    controller = HysteresisControllerAgent(
        agent_id='PumpController',
        kernel=host,
        low_threshold=3.0,
        high_threshold=8.0,
        input_topic='state/tank/level',
        output_topic='cmd/pump/on_off'
    )

    # 4. 添加到主机
    host.add_agents([tank, pump, inflow, controller])

    # 5. 仿真循环 (手动模拟消息总线)
    # 因为我们的 Tank 和 Pump 模型不是原生的 "Agent"，
    # 我们在循环中手动模拟消息的发布和订阅来展示概念。
    num_steps = 600
    pump_status_history = []

    print("Running simulation with custom agent...")
    # 手动调用一次 setup 来激活订阅
    controller.setup()

    for i in range(num_steps):
        # a) Tank 发布自己的状态
        tank_level = tank.get_port('level').value
        # 在真实的Agent系统中，这会是一个publish调用
        controller.on_message(Message(topic='state/tank/level', payload={'value': tank_level}))

        # b) 所有智能体执行自己的逻辑
        host.step(dt=1.0)

        # c) Pump 接收控制指令
        # 在真实的Agent系统中，Pump会有一个on_message来处理这个
        pump_command = controller.current_output
        pump.set_input('num_pumps_on', pump_command)

        # d) 设置泵的物理边界
        pump.set_input('inlet_level', tank.level)
        pump.set_input('outlet_level', 10.0) # 假设泵送到10m高处

        # e) 更新物理连接
        tank.set_input('inflow', inflow.get_port('value').value)
        tank.set_input('release_outflow', pump.get_port('flow').value)

        pump_status_history.append(pump_command)
    print("Simulation finished.")

    # 6. 绘图
    results_df = host.get_datalogger().get_as_dataframe()
    results_df['pump_status'] = pump_status_history

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    fig.suptitle('第三十一章: 自定义智能体 (滞回控制器) 仿真', fontsize=16)

    ax1.plot(results_df.index, results_df['MyTank.level'], 'b-', label='水箱水位')
    ax1.axhline(y=8.0, color='r', linestyle='--', label='关闭水泵水位 (8m)')
    ax1.axhline(y=3.0, color='g', linestyle='--', label='开启水泵水位 (3m)')
    ax1.set_ylabel('水位 (m)'); ax1.legend(); ax1.grid(True)

    ax2.plot(results_df.index, results_df['pump_status'], 'm-', drawstyle='steps-post', label='水泵状态 (On/Off)')
    ax2.set_xlabel('时间 (秒)'); ax2.set_ylabel('水泵指令'); ax2.legend(); ax2.grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95]); plt.show()


if __name__ == "__main__":
    run_simulation_with_custom_agent()
