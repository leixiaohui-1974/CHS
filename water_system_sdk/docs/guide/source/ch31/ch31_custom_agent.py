import matplotlib.pyplot as plt
import pandas as pd

# This is a simple way to make the SDK accessible to the script.
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src')))

from chs_sdk.core.host import AgentKernel
from chs_sdk.agents.base import BaseAgent
from chs_sdk.agents.message import Message
from chs_sdk.modules.modeling.storage_models import LinearTank
from chs_sdk.modules.modeling.control_structure_models import PumpStationModel
from chs_sdk.modules.disturbances.predefined import Disturbance

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

    def on_execute(self, current_time: float, time_step: float):
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
    kernel = AgentKernel()

    # 2. 创建物理组件 (这些不是Agent, 手动管理)
    tank = LinearTank(name='MyTank', area=1000.0, initial_level=5.0)
    pump = PumpStationModel(name='MyPump', num_pumps_total=1, curve_coeffs=[-0.01, 0.1, 15])
    inflow = Disturbance(signal_type='constant', value=0.2, name='Inflow') # 恒定入流

    # 3. 将我们的自定义控制器添加到内核
    # 内核会负责创建实例
    kernel.add_agent(
        agent_class=HysteresisControllerAgent,
        agent_id='PumpController',
        low_threshold=3.0,
        high_threshold=8.0,
        input_topic='state/tank/level',
        output_topic='cmd/pump/on_off'
    )
    # 获取对已创建的agent实例的引用
    controller = kernel._agents['PumpController']

    # 5. 仿真循环 (手动模拟 + 手动数据记录)
    # 因为我们的 Tank 和 Pump 模型不是原生的 "Agent"，
    # 我们在循环中手动模拟消息的发布和订阅，并手动记录数据。
    num_steps = 600
    time_history = []
    tank_level_history = []
    pump_status_history = []

    print("Running simulation with custom agent...")
    # 启动内核，这将调用所有智能体的 setup()
    kernel.start(time_step=1.0)

    for i in range(num_steps):
        # a) Tank "发布" 自己的状态 (手动调用 on_message)
        tank_level = tank.output
        controller.on_message(Message(topic='state/tank/level', payload={'value': tank_level}, sender_id=tank.name))

        # b) 内核执行所有智能体的逻辑 (controller.execute)
        kernel.tick()

        # c) "接收" 控制指令并更新模型状态
        pump_command = controller.current_output
        pump.num_pumps_on = pump_command

        # d) 更新物理模型的输入和连接
        tank.input.inflow = inflow.output
        tank.input.release_outflow = pump.output

        # e) 步进物理模型
        pump.step(inlet_pressure=tank.level, outlet_pressure=10.0)
        tank.step(dt=1.0)
        inflow.step(t=i)

        # f) 手动记录数据
        time_history.append(i * 1.0)
        tank_level_history.append(tank_level)
        pump_status_history.append(pump_command)

    kernel.stop()
    print("Simulation finished.")

    # 6. 绘图
    # 从我们手动记录的列表中创建DataFrame
    results_df = pd.DataFrame({
        'time': time_history,
        'tank_level': tank_level_history,
        'pump_status': pump_status_history
    })

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    fig.suptitle('第三十一章: 自定义智能体 (滞回控制器) 仿真', fontsize=16)

    ax1.plot(results_df['time'], results_df['tank_level'], 'b-', label='水箱水位')
    ax1.axhline(y=8.0, color='r', linestyle='--', label='关闭水泵水位 (8m)')
    ax1.axhline(y=3.0, color='g', linestyle='--', label='开启水泵水位 (3m)')
    ax1.set_ylabel('水位 (m)'); ax1.legend(); ax1.grid(True)

    ax2.plot(results_df['time'], results_df['pump_status'], 'm-', drawstyle='steps-post', label='水泵状态 (On/Off)')
    ax2.set_xlabel('时间 (秒)'); ax2.set_ylabel('水泵指令'); ax2.legend(); ax2.grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95]); plt.show()


if __name__ == "__main__":
    run_simulation_with_custom_agent()
