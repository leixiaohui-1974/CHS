import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# This is a simple way to make the SDK accessible to the script.
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..')))
import pandas as pd

from chs_sdk.core.host import AgentKernel as Host
from chs_sdk.agents.base import BaseAgent
from chs_sdk.agents.message import Message
from chs_sdk.modules.modeling.storage_models import LinearTank
from chs_sdk.modules.modeling.control_structure_models import PumpStationModel
from chs_sdk.modules.disturbances.predefined import Disturbance
from water_system_sdk.docs.guide.source.project_utils import ModelAgent

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
    host = Host()

    # 2. 创建物理组件的智能体封装
    host.add_agent(agent_class=ModelAgent, agent_id='MyTank', model_class=LinearTank, area=1000.0, initial_level=5.0)
    host.add_agent(agent_class=ModelAgent, agent_id='MyPump', model_class=PumpStationModel, num_pumps_total=1, curve_coeffs=[-0.01, 0.1, 15], default_inputs={'outlet_pressure': 10.0})
    host.add_agent(agent_class=ModelAgent, agent_id='Inflow', model_class=Disturbance, signal_type='constant', value=0.2)

    # 3. 创建我们的自定义控制器实例
    host.add_agent(
        agent_class=HysteresisControllerAgent,
        agent_id='PumpController',
        low_threshold=3.0,
        high_threshold=8.0,
        input_topic='MyTank/level',
        output_topic='MyPump/num_pumps_on'
    )

    # 4. 建立连接
    tank_agent = host._agents['MyTank']
    pump_agent = host._agents['MyPump']
    inflow_agent = host._agents['Inflow']
    controller_agent = host._agents['PumpController']

    # Pump subscribes to controller command
    pump_agent.subscribe(topic='PumpController/output', port_name='num_pumps_on')
    # Pump needs tank level for its calculation
    pump_agent.subscribe(topic='MyTank/level', port_name='inlet_pressure')
    # Tank subscribes to inflow
    tank_agent.subscribe(topic='Inflow/output', port_name='inflow')
    # Tank subscribes to pump outflow
    tank_agent.subscribe(topic='MyPump/flow', port_name='release_outflow')


    # 5. 仿真循环
    num_steps = 600
    dt = 1.0
    results = []
    host.start(time_step=dt)
    print("Running simulation with custom agent...")
    for i in range(num_steps):
        host.tick()
        results.append({
            'time': host.current_time,
            'tank_level': tank_agent.model.level,
            'pump_flow': pump_agent.model.flow,
            'pump_status': pump_agent.model.num_pumps_on,
        })
    print("Simulation finished.")

    # 6. 绘图
    results_df = pd.DataFrame(results)

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
