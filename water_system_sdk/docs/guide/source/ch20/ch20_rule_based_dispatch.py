import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
import pandas as pd
import sys
import os
import numpy as np

# This is a simple way to make the SDK accessible to the script.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..')))

from chs_sdk.core.host import AgentKernel as Host
from chs_sdk.modules.modeling.storage_models import FixedLinearTank
from chs_sdk.modules.modeling.control_structure_models import SluiceGate, PumpStationModel
from chs_sdk.modules.control.rule_based_controller import RuleBasedOperationalController
from chs_sdk.modules.disturbances.timeseries_disturbance import TimeSeriesDisturbance
from water_system_sdk.docs.guide.source.project_utils import ModelAgent



def run_simulation():
    """
    This script demonstrates how to use a RuleBasedOperationalController
    to implement operational dispatch logic for a reservoir.
    """
    host = Host()

    # 1. 创建组件 - 使用FixedLinearTank确保水量平衡计算正确
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='MainReservoir',
        model_class=FixedLinearTank,
        area=1000.0,  # 减小水库面积，让水位变化更明显
        initial_level=1.5)  # 初始水位1.5米，触发兴利蓄水规则
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='InletGate',
        model_class=SluiceGate,
        gate_width=2.0,
        discharge_coeff=0.8,
        slew_rate=1.0/60.0) # Assume 60s travel time
    # 创建一个自定义的PumpAgent来正确处理参数映射
    class PumpAgent(ModelAgent):
        def on_execute(self, current_time, time_step, extra_state=None):
            # 获取水位信息作为压力
            reservoir_level = self.input_values.get('MainReservoir/level', 0.0)
            pump_command = self.input_values.get('command', 0)
            
            # 将水位转换为压力（简化：假设1m水位 = 9.81 kPa压力）
            inlet_pressure = 0.0  # 假设入口压力为0（大气压）
            outlet_pressure = reservoir_level * 9.81  # 出口压力与水位成正比
            
            # 水泵数量根据命令确定
            num_pumps_on = int(pump_command) * self.model.num_pumps_total
            
            # 调用模型的step方法
            self.model.step(
                inlet_pressure=inlet_pressure,
                outlet_pressure=outlet_pressure,
                num_pumps_on=num_pumps_on
            )
            
            # 发布输出
            if hasattr(self.model, 'get_state') and callable(self.model.get_state):
                output = self.model.get_state()
                print(f"[{self.agent_id}] get_state() returned: {output}")
                if isinstance(output, dict):
                    for key, value in output.items():
                        print(f"[{self.agent_id}] Publishing {key}={value} to topic '{self.agent_id}/{key}'")
                        self._publish(f"{self.agent_id}/{key}", value)
        
        def on_message(self, message):
            """处理接收到的消息"""
            print(f"[{self.agent_id}] Received message: topic='{message.topic}' payload={message.payload}")
            if message.topic == 'MainReservoir/level':
                self.input_values['MainReservoir/level'] = message.payload
            elif message.topic == 'ReservoirDispatcher/pump_command':
                self.input_values['command'] = message.payload
                print(f"[{self.agent_id}] Stored pump command={message.payload}")

    host.add_agent(
        agent_class=PumpAgent,
        agent_id='OutletPump',
        model_class=PumpStationModel,
        num_pumps_total=2,
        curve_coeffs=[0.0, 0.1, 0.0],  # 简化的线性曲线：Q = 0.1 * H
        initial_num_pumps_on=0)  # 初始状态：水泵关闭
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='UpstreamInflow',
        model_class=TimeSeriesDisturbance,
        times=[0, 100, 101, 1000],  # 提前来水时间
        values=[5, 5, 30, 30])      # 增加来水量，让水位更快上升

    rules = [
        {"if": [{"variable": "MainReservoir.level", "operator": ">", "value": 15.0}], "then": {"gate_opening": 0.0, "pump_command": 1}},
        {"if": [{"variable": "MainReservoir.level", "operator": "<", "value": 3.0}], "then": {"gate_opening": 1.0, "pump_command": 0}},
    ]
    default_actions = {"gate_opening": 0.5, "pump_command": 0}
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='ReservoirDispatcher',
        model_class=RuleBasedOperationalController,
        rules=rules,
        default_actions=default_actions)

    # 2. 建立连接
    reservoir_agent = host._agents['MainReservoir']
    gate_agent = host._agents['InletGate']
    pump_agent = host._agents['OutletPump']
    inflow_agent = host._agents['UpstreamInflow']
    dispatcher_agent = host._agents['ReservoirDispatcher']

    gate_agent.subscribe(f"{dispatcher_agent.agent_id}/gate_opening", 'command')
    pump_agent.subscribe(f"{dispatcher_agent.agent_id}/pump_command", 'num_pumps_on')

    gate_agent.input_values['upstream_level'] = 20.0
    gate_agent.subscribe(f"{reservoir_agent.agent_id}/level", 'downstream_level')

    pump_agent.subscribe(f"{reservoir_agent.agent_id}/level", 'inlet_pressure')
    pump_agent.input_values['outlet_pressure'] = 2.0

    reservoir_agent.subscribe(f"{gate_agent.agent_id}/output", 'gate_inflow')
    reservoir_agent.subscribe(f"{inflow_agent.agent_id}/output", 'inflow')
    reservoir_agent.subscribe(f"{pump_agent.agent_id}/output", 'release_outflow')

    # 5. 运行仿真
    print("开始运行水库调度仿真...")
    num_steps = 1000
    dt = 1.0
    results = []
    host.start(time_step=dt)
    
    for i in range(num_steps):
        host.tick()
        
        # 收集所有代理的状态
        step_result = {
            'time': host.current_time,
            'MainReservoir': {
                'level': reservoir_agent.model.level,
                'volume': reservoir_agent.model.level * reservoir_agent.model.area
            },
            'InletGate': {
                'actual_position': gate_agent.model.get_current_position(),
                'target_setpoint': gate_agent.model.target_setpoint,
                'current_setpoint': gate_agent.model.state.current_setpoint
            },
            'OutletPump': {
                'flow': pump_agent.model.flow,
                'num_pumps_on': pump_agent.model.num_pumps_on,
                'output': pump_agent.model.output
            },
            'UpstreamInflow': {
                'output': inflow_agent.model.output
            },
            'ReservoirDispatcher': {
                'gate_opening': dispatcher_agent.model.current_actions.get('gate_opening', 0),
                'pump_command': dispatcher_agent.model.current_actions.get('pump_command', 0)
            }
        }
        results.append(step_result)
    
    # 6. 结果可视化
    print("生成可视化结果...")
    
    # 设置全局字体大小
    plt.rcParams['font.size'] = 12
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['axes.labelsize'] = 12
    plt.rcParams['xtick.labelsize'] = 10
    plt.rcParams['ytick.labelsize'] = 10
    plt.rcParams['legend.fontsize'] = 11
    
    # 创建2x3的子图布局
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('水库调度系统仿真结果', fontsize=18, fontweight='bold')
    
    # 提取数据
    times = [step['time'] for step in results]
    reservoir_levels = [step['MainReservoir']['level'] for step in results]
    reservoir_volumes = [step['MainReservoir']['volume'] for step in results]
    gate_openings = [step['InletGate']['actual_position'] for step in results]
    pump_flows = [step['OutletPump']['flow'] for step in results]
    pump_nums = [step['OutletPump']['num_pumps_on'] for step in results]
    upstream_inflows = [step['UpstreamInflow']['output'] for step in results]
    dispatcher_gate = [step['ReservoirDispatcher']['gate_opening'] for step in results]
    dispatcher_pump = [step['ReservoirDispatcher']['pump_command'] for step in results]
    
    # 计算净流量
    net_flows = [inflow - pump_flow for inflow, pump_flow in zip(upstream_inflows, pump_flows)]
    
    # 图1: 水位变化趋势
    ax1 = axes[0, 0]
    ax1.plot(times, reservoir_levels, 'b-', linewidth=2, label='水库水位')
    ax1.axhline(y=15.0, color='r', linestyle='--', alpha=0.7, label='汛限水位 (15m)')
    ax1.axhline(y=3.0, color='orange', linestyle='--', alpha=0.7, label='兴利水位 (3m)')
    ax1.fill_between(times, 15.0, max(reservoir_levels), alpha=0.2, color='red', label='防洪区域')
    ax1.fill_between(times, 0, 3.0, alpha=0.2, color='orange', label='兴利区域')
    ax1.fill_between(times, 3.0, 15.0, alpha=0.2, color='green', label='正常运行区域')
    ax1.set_xlabel('时间 (s)')
    ax1.set_ylabel('水位 (m)')
    ax1.set_title('水库水位变化趋势')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 图2: 流量平衡分析
    ax2 = axes[0, 1]
    # 上游来水用实线（最粗，最高层级）
    ax2.plot(times, upstream_inflows, 'g-', linewidth=4, label='上游来水', zorder=4)
    # 水泵出流用点状线
    ax2.plot(times, pump_flows, 'r:', linewidth=2, label='水泵出流', zorder=2)
    ax2.scatter(times[::50], [pump_flows[i] for i in range(0, len(pump_flows), 50)], 
                color='red', s=30, alpha=0.8, zorder=5)
    # 净流量用虚线+点（最细，最低层级）
    ax2.plot(times, net_flows, 'b--', linewidth=1.5, label='净流量', zorder=1)
    ax2.scatter(times[::100], [net_flows[i] for i in range(0, len(net_flows), 100)], 
                color='blue', s=25, alpha=0.8, zorder=5)
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5, zorder=1)
    ax2.set_xlabel('时间 (s)')
    ax2.set_ylabel('流量 (m^3/s)')
    ax2.set_title('流量平衡分析')
    ax2.legend()
    ax2.grid(True, alpha=0.15, color='lightgray')
    
    # 图3: 调度规则触发状态
    ax3 = axes[0, 2]
    # 创建调度状态数组
    dispatch_states = []
    for level in reservoir_levels:
        if level > 15.0:
            dispatch_states.append(2)  # 防洪状态
        elif level < 3.0:
            dispatch_states.append(0)  # 兴利状态
        else:
            dispatch_states.append(1)  # 正常运行
    
    colors = ['orange', 'green', 'red']
    labels = ['兴利蓄水', '正常运行', '防洪泄水']
    for i, (color, label) in enumerate(zip(colors, labels)):
        mask = [s == i for s in dispatch_states]
        if any(mask):
            ax3.scatter([t for t, m in zip(times, mask) if m], 
                       [l for l, m in zip(reservoir_levels, mask) if m], 
                       c=color, s=20, alpha=0.7, label=label)
    
    ax3.axhline(y=15.0, color='r', linestyle='--', alpha=0.7)
    ax3.axhline(y=3.0, color='orange', linestyle='--', alpha=0.7)
    ax3.set_xlabel('时间 (s)')
    ax3.set_ylabel('水位 (m)')
    ax3.set_title('调度规则触发状态')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 图4: 闸门控制对比（命令 vs 实际）
    ax4 = axes[1, 0]
    
    # 绘制闸门开度命令（点）和实际开度（线）
    ax4.plot(times, gate_openings, 'b-', linewidth=2, label='闸门实际开度', alpha=0.8)
    ax4.scatter(times[::50], [dispatcher_gate[i] for i in range(0, len(dispatcher_gate), 50)], 
                color='red', s=30, label='闸门开度命令', alpha=0.7, zorder=5)
    
    ax4.set_xlabel('时间 (s)')
    ax4.set_ylabel('闸门开度')
    ax4.set_title('闸门控制效果对比')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.set_ylim(-0.1, 1.1)
    
    # 图5: 水泵控制对比（命令 vs 实际出水量）
    ax5 = axes[1, 1]
    ax5_twin = ax5.twinx()
    
    # 绘制实际出水量（左轴，红色线）
    line1 = ax5.plot(times, pump_flows, 'r-', linewidth=2, label='实际出水量', alpha=0.8)
    # 绘制水泵命令（右轴，蓝色散点）
    line2 = ax5_twin.scatter(times[::50], [dispatcher_pump[i] * 2 for i in range(0, len(dispatcher_pump), 50)], 
                             color='blue', s=30, label='水泵命令', alpha=0.7, zorder=5)
    
    ax5.set_xlabel('时间 (s)')
    ax5.set_ylabel('实际出水量 (m^3/s)', color='r')
    ax5_twin.set_ylabel('水泵命令', color='b')
    ax5.set_title('水泵控制效果对比')
    
    # 设置左轴（流量）范围
    max_flow = max(pump_flows) if pump_flows else 0
    ax5.set_ylim(-max_flow * 0.05, max_flow * 1.1)
    
    # 设置右轴（水泵数量）范围
    ax5_twin.set_ylim(-0.2, 2.5)
    
    # 合并图例
    lines = line1 + [line2]
    labels = [l.get_label() if hasattr(l, 'get_label') else '水泵命令' for l in lines]
    ax5.legend(lines, labels, loc='upper left')
    ax5.grid(True, alpha=0.3)
    
    # 图6: 系统性能评估
    ax6 = axes[1, 2]
    
    # 计算水位变化率
    level_changes = []
    for i in range(1, len(reservoir_levels)):
        change_rate = (reservoir_levels[i] - reservoir_levels[i-1]) / 1.0  # 每秒变化率
        level_changes.append(change_rate)
    
    # 添加初始值
    level_changes.insert(0, 0)
    
    ax6.plot(times, level_changes, 'purple', linewidth=2, label='水位变化率')
    ax6.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    ax6.fill_between(times, level_changes, 0, 
                     where=[c > 0 for c in level_changes], 
                     alpha=0.3, color='red', label='水位上升')
    ax6.fill_between(times, level_changes, 0, 
                     where=[c < 0 for c in level_changes], 
                     alpha=0.3, color='blue', label='水位下降')
    
    ax6.set_xlabel('时间 (s)')
    ax6.set_ylabel('水位变化率 (m/s)')
    ax6.set_title('系统性能评估')
    ax6.legend()
    ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    # 7. 输出统计信息
    print("\n" + "="*60)
    print("水库调度仿真结果统计")
    print("="*60)
    print(f"仿真时长: {len(times)} 秒")
    print(f"初始水位: {reservoir_levels[0]:.3f} m")
    print(f"最终水位: {reservoir_levels[-1]:.3f} m")
    print(f"水位变化: {reservoir_levels[-1] - reservoir_levels[0]:.3f} m")
    print(f"平均上游来水: {np.mean(upstream_inflows):.2f} m³/s")
    print(f"平均水泵出流: {np.mean(pump_flows):.2f} m³/s")
    print(f"平均净流量: {np.mean(net_flows):.2f} m³/s")
    
    # 统计调度状态
    flood_count = sum(1 for s in dispatch_states if s == 2)
    normal_count = sum(1 for s in dispatch_states if s == 1)
    storage_count = sum(1 for s in dispatch_states if s == 0)
    
    print(f"\n调度状态统计:")
    print(f"防洪状态: {flood_count} 秒 ({flood_count/len(dispatch_states)*100:.1f}%)")
    print(f"正常运行: {normal_count} 秒 ({normal_count/len(dispatch_states)*100:.1f}%)")
    print(f"兴利蓄水: {storage_count} 秒 ({storage_count/len(dispatch_states)*100:.1f}%)")
    
    print("="*60)

if __name__ == "__main__":
    run_simulation()
