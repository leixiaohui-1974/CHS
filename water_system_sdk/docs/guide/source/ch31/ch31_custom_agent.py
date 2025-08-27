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
from chs_sdk.modules.modeling.storage_models import FixedLinearTank
from chs_sdk.modules.modeling.control_structure_models import PumpStationModel
from chs_sdk.modules.disturbances.predefined import Disturbance
from water_system_sdk.docs.guide.source.project_utils import ModelAgent, EnhancedModelAgent
import numpy as np

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
            # 支持多种消息格式：直接数值或字典格式
            if isinstance(message.payload, dict):
                self.current_input = message.payload.get('value', 0.0)
            else:
                # 直接数值格式
                self.current_input = float(message.payload)

    def on_execute(self, current_time: float, time_step: float):
        # 在每个时间步执行控制逻辑
        output_before = self.current_output
        if self.current_input > self.high_threshold:
            self.current_output = 1 # 高于上限，开启水泵排水
        elif self.current_input < self.low_threshold:
            self.current_output = 0 # 低于下限，关闭水泵
        # 如果在中间，则保持 self.current_output 不变

        if self.current_output != output_before:
            print(f"[{current_time:.0f}s] {self.agent_id}: Input is {self.current_input:.2f}, changing output to {self.current_output}")

        # 发布控制指令 - 发布简单数值而不是字典
        self._publish(self.output_topic, self.current_output)

def run_simulation_with_custom_agent():
    """
    This script demonstrates how to use the custom HysteresisControllerAgent
    to control a pump based on a tank's water level.
    """
    host = Host()

    # 2. 创建物理组件的智能体封装 - 使用修复版LinearTank，调整参数让滞回控制器能展示完整循环
    host.add_agent(agent_class=ModelAgent, agent_id='MyTank', model_class=FixedLinearTank, area=1000.0, initial_level=4.5)  # 在阈值之间开始
    host.add_agent(agent_class=EnhancedModelAgent, agent_id='MyPump', model_class=PumpStationModel, num_pumps_total=1, curve_coeffs=[-0.001, 0.05, 5], initial_num_pumps_on=0)  # 降低水泵功率
    host.add_agent(agent_class=ModelAgent, agent_id='Inflow', model_class=Disturbance, signal_type='constant', value=2.0)  # 增加入流

    # 3. 创建我们的自定义控制器实例 - 调整阈值让效果更明显
    host.add_agent(
        agent_class=HysteresisControllerAgent,
        agent_id='PumpController',
        low_threshold=3.0,   # 低于3.0m开启水泵
        high_threshold=6.0,  # 高于6.0m关闭水泵
        input_topic='MyTank/level',
        output_topic='cmd/pump/num_pumps_on'
    )

    # 4. 建立连接
    tank_agent = host._agents['MyTank']
    pump_agent = host._agents['MyPump']
    inflow_agent = host._agents['Inflow']
    controller_agent = host._agents['PumpController']

    # 为泵站设置默认的outlet_pressure - 需要在input_values中设置
    pump_agent.input_values['outlet_pressure'] = 10.0
    # 设置初始的num_pumps_on
    pump_agent.input_values['num_pumps_on'] = 0
    # 设置初始的inlet_pressure
    pump_agent.input_values['inlet_pressure'] = 4.5  # 初始水箱水位

    # Pump subscribes to controller command
    pump_agent.subscribe(topic='cmd/pump/num_pumps_on', port_name='num_pumps_on')
    # Pump needs tank level for its calculation
    pump_agent.subscribe(topic='MyTank/level', port_name='inlet_pressure')
    # Tank subscribes to inflow
    tank_agent.subscribe(topic='Inflow/output', port_name='inflow')
    # Tank subscribes to pump outflow
    tank_agent.subscribe(topic='MyPump/flow', port_name='release_outflow')


    # 5. 仿真循环 - 使用类似ch24/ch25的控制模式，增加仿真时长观察完整循环
    num_steps = 2400  # 增加到40分钟，观察多个完整的滞回循环
    dt = 1.0
    results = []
    host.start(time_step=dt)
    print("Running simulation with custom agent...")
    
    for i in range(num_steps):
        # 获取当前水位
        current_tank_level = tank_agent.model.level
        
        # 手动更新控制器的输入并执行控制逻辑
        controller_agent.current_input = current_tank_level
        
        # 执行滞回控制逻辑（修正：高水位开启水泵排水）
        output_before = controller_agent.current_output
        if controller_agent.current_input > controller_agent.high_threshold:
            controller_agent.current_output = 1  # 高于上限，开启水泵排水
        elif controller_agent.current_input < controller_agent.low_threshold:
            controller_agent.current_output = 0  # 低于下限，关闭水泵
        # 如果在中间，则保持 controller_agent.current_output 不变

        if controller_agent.current_output != output_before:
            print(f"[{host.current_time:.0f}s] {controller_agent.agent_id}: Input is {controller_agent.current_input:.2f}, changing output to {controller_agent.current_output}")

        # 直接设置泵的控制指令
        pump_agent.input_values['num_pumps_on'] = controller_agent.current_output
        pump_agent.input_values['inlet_pressure'] = current_tank_level
        
        # 执行仿真步进
        host.tick()
        
        # 记录结果
        results.append({
            'time': host.current_time,
            'tank_level': tank_agent.model.level,
            'pump_flow': pump_agent.model.flow,
            'pump_status': pump_agent.model.num_pumps_on,
            'controller_output': controller_agent.current_output,
        })
        
    print("Simulation finished.")

    # 6. 绘图
    results_df = pd.DataFrame(results)

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12), sharex=True)
    fig.suptitle('第三十一章: 自定义智能体 (滞回控制器) 仿真', fontsize=16)

    # 水位图
    ax1.plot(results_df['time'], results_df['tank_level'], 'b-', linewidth=2, label='水箱水位')
    ax1.axhline(y=6.0, color='r', linestyle='--', linewidth=1.5, label='开启水泵排水位 (6m)')
    ax1.axhline(y=3.0, color='g', linestyle='--', linewidth=1.5, label='关闭水泵水位 (3m)')
    ax1.set_ylabel('水位 (m)'); ax1.legend(); ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, 8)

    # 水泵状态图
    ax2.plot(results_df['time'], results_df['pump_status'], 'm-', drawstyle='steps-post', linewidth=2, label='水泵状态 (On/Off)')
    ax2.plot(results_df['time'], results_df['controller_output'], 'c--', drawstyle='steps-post', linewidth=1.5, alpha=0.7, label='控制器输出')
    ax2.set_ylabel('水泵指令'); ax2.legend(); ax2.grid(True, alpha=0.3)
    ax2.set_ylim(-0.1, 1.1)
    
    # 水泵流量图
    ax3.plot(results_df['time'], results_df['pump_flow'], 'orange', linewidth=2, label='水泵流量')
    ax3.set_xlabel('时间 (秒)'); ax3.set_ylabel('流量 (m³/s)'); ax3.legend(); ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0, max(results_df['pump_flow']) * 1.1 if max(results_df['pump_flow']) > 0 else 20)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # # 保存图形到文件
    # plt.savefig('ch31_hysteresis_controller_results.png', dpi=300, bbox_inches='tight')
    # print("\n=== 仿真结果图表已保存为 ch31_hysteresis_controller_results.png ===")
    
    # 显示图形（如果在GUI环境中）
    try:
        plt.show()
    except Exception as e:
        print(f"无法显示图形: {e}")
    
    # 打印仿真统计信息
    print("\n=== 滞回控制器仿真统计 ===")
    print(f"仿真时长: {num_steps} 秒 ({num_steps/60:.1f} 分钟)")
    print(f"低位阈值: {controller_agent.low_threshold}m")
    print(f"高位阈值: {controller_agent.high_threshold}m")
    
    min_tank_level = min(results_df['tank_level'])
    max_tank_level = max(results_df['tank_level'])
    pump_on_steps = sum(1 for status in results_df['pump_status'] if status > 0)
    pump_on_time = pump_on_steps * dt
    
    print(f"\n=== 关键指标 ===")
    print(f"水箱最低水位: {min_tank_level:.2f} m")
    print(f"水箱最高水位: {max_tank_level:.2f} m")
    print(f"水泵运行时间: {pump_on_time:.0f} 秒 ({pump_on_time/60:.1f} 分钟)")
    print(f"水泵运行比例: {pump_on_time/num_steps*100:.1f}%")
    
    # 检查滞回控制是否正常工作
    controller_changes = sum(1 for i in range(1, len(results_df)) 
                           if results_df.iloc[i]['controller_output'] != results_df.iloc[i-1]['controller_output'])
    print(f"控制器状态变化次数: {controller_changes}")
        
    return results_df


if __name__ == "__main__":
    run_simulation_with_custom_agent()
