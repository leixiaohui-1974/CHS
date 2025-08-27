import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
import numpy as np
import pandas as pd
import sys
import os

# 添加正确的模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'docs', 'guide', 'source'))

from chs_sdk.core.host import AgentKernel as Host
from chs_sdk.modules.modeling.storage_models import NonlinearTank
from chs_sdk.modules.disturbances.timeseries_disturbance import TimeSeriesDisturbance
from chs_sdk.modules.control.rule_based_controller import RuleBasedOperationalController
from chs_sdk.modules.control.dynamic_outflow_controller import DynamicOutflowController
from project_utils import ModelAgent, LevelSensor

def run_simulation():
    """
    This script demonstrates how to use the NonlinearTank model to simulate
    a reservoir with an irregular shape, defined by a level-volume curve.
    Now with intelligent agents for water level monitoring and spillway control.
    """
    host = Host()

    # 1. 定义水位-库容曲线 (水位从10米开始，更合理)
    # 更非线性的曲线：低水位时库容变化缓慢，高水位时库容变化快速
    level_volume_curve = np.array([
        [10.0, 10.2, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0, 15.0],  # 水位
        [0.0,  5e3, 2e4, 6e4, 1.2e5, 2.5e5, 4.5e5, 7.5e5, 11e5, 15e5, 25e5]  # 库容
    ])

    # 2. 创建组件 - 初始水位设为10.5米，在水位-库容曲线范围内
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='IrregularReservoir',
        model_class=NonlinearTank,
        level_to_volume=level_volume_curve,
        initial_level=10.5)

    # 洪水入流过程：0-12小时逐渐增加到50m³/s，然后逐渐减少
    inflow_times_hours = [0, 12, 24, 36, 48]
    inflow_times_seconds = [t * 3600 for t in inflow_times_hours]
    inflow_values = [5, 50, 20, 10, 9]  # m³/s
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='FloodInflow',
        model_class=TimeSeriesDisturbance,
        times=inflow_times_seconds,
        values=inflow_values)

    # 恒定生态基流出流：10 m³/s
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='BaseOutflow',
        model_class=TimeSeriesDisturbance,
        times=[0],
        values=[-10.0])  # 负值表示出流

    # 3. 创建智能体系统
    # 3.1 水位监测智能体
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='LevelMonitor',
        model_class=LevelSensor)

    # 3.2 调蓄决策智能体（基于规则的控制器）
    # 定义调蓄规则：水位超过阈值时增加出流（更积极的调蓄策略）
    spillway_rules = [
        {
            'if': [{'variable': 'IrregularReservoir.state.level', 'operator': '>', 'value': 13.0}],
            'then': {'outflow_multiplier': 6.0, 'emergency_release': True}  # 高水位紧急泄洪，6倍出流
        },
        {
            'if': [{'variable': 'IrregularReservoir.state.level', 'operator': '>', 'value': 12.5}],
            'then': {'outflow_multiplier': 5.0, 'emergency_release': False}  # 高水位5倍出流
        },
        {
            'if': [{'variable': 'IrregularReservoir.state.level', 'operator': '>', 'value': 12.0}],
            'then': {'outflow_multiplier': 4.0, 'emergency_release': False}  # 中等水位4倍出流
        },
        {
            'if': [{'variable': 'IrregularReservoir.state.level', 'operator': '>', 'value': 11.5}],
            'then': {'outflow_multiplier': 3.0, 'emergency_release': False}  # 低水位3倍出流
        }
    ]
    
    default_actions = {'outflow_multiplier': 1.0, 'emergency_release': False}  # 默认正常出流
    
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='SpillwayController',
        model_class=RuleBasedOperationalController,
        rules=spillway_rules,
        default_actions=default_actions)

    # 3.3 动态出流控制器（执行调蓄决策）
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='DynamicOutflowController',
        model_class=DynamicOutflowController,
        base_outflow=10.0,  # 基础出流量增加到10 m³/s
        max_outflow_multiplier=8.0)  # 最大出流倍数增加到8倍

    # 4. 建立连接
    reservoir_agent = host._agents['IrregularReservoir']
    inflow_agent = host._agents['FloodInflow']
    base_outflow_agent = host._agents['BaseOutflow']
    level_monitor_agent = host._agents['LevelMonitor']
    spillway_agent = host._agents['SpillwayController']
    dynamic_outflow_agent = host._agents['DynamicOutflowController']

    # 4.1 基本连接
    reservoir_agent.subscribe(f"{inflow_agent.agent_id}/output", 'inflow')
    # 水库现在使用动态出流控制器的输出，而不是固定的BaseOutflow
    # 注意：需要订阅current_outflow topic，这是DynamicOutflowController实际发布的
    print(f"[DEBUG] Setting up reservoir subscription to {dynamic_outflow_agent.agent_id}/current_outflow")
    reservoir_agent.subscribe(f"{dynamic_outflow_agent.agent_id}/current_outflow", 'release_outflow')

    # 4.2 智能体连接
    # 水位监测智能体订阅水库水位（LevelSensor需要true_value参数）
    level_monitor_agent.subscribe(topic=f"{reservoir_agent.agent_id}/level", port_name='true_value')
    
    # 调蓄决策智能体订阅水位监测智能体的输出
    spillway_agent.subscribe(topic=f"{level_monitor_agent.agent_id}/output", port_name='level_input')
    
    # 动态出流控制器订阅调蓄决策智能体的输出
    # 由于RuleBasedOperationalController发布的是字典的各个键作为独立topics
    # 我们需要创建一个聚合函数或者修改DynamicOutflowController来处理多个输入
    print(f"[DEBUG] Setting up DynamicOutflowController subscription to {spillway_agent.agent_id}/outflow_multiplier")
    dynamic_outflow_agent.subscribe(topic=f"{spillway_agent.agent_id}/outflow_multiplier", port_name='outflow_multiplier_input')
    dynamic_outflow_agent.subscribe(topic=f"{spillway_agent.agent_id}/emergency_release", port_name='emergency_release_input')

    # 5. 运行仿真
    num_steps = 48 * 60  # 48小时，每分钟一个步长
    dt = 60.0  # 60秒
    results = []
    
    print(f"开始仿真：")
    print(f"- 初始水位: {reservoir_agent.model.level:.2f} m")
    print(f"- 初始库容: {reservoir_agent.model.volume:.0f} m³")
    print(f"- 时间步长: {dt} s")
    print(f"- 仿真时长: {num_steps * dt / 3600:.1f} 小时")
    print(f"- 智能体系统: 水位监测 + 调蓄决策")
    
    host.start(time_step=dt)
    
    for i in range(num_steps):
        host.tick()
        
        # 获取智能体状态
        spillway_actions = spillway_agent.model.current_actions
        current_level = reservoir_agent.model.level
        
        # 获取动态出流控制器的状态
        dynamic_outflow_state = dynamic_outflow_agent.model.get_state()
        current_dynamic_outflow = dynamic_outflow_state['current_outflow']
        
        # 记录结果
        results.append({
            'time': host.current_time,
            'IrregularReservoir.level': reservoir_agent.model.level,
            'IrregularReservoir.volume': reservoir_agent.model.volume,
            'FloodInflow.value': inflow_agent.model.output,
            'BaseOutflow.value': base_outflow_agent.model.output,
            'DynamicOutflow.value': -current_dynamic_outflow,  # 负值表示出流
            'DynamicOutflow.multiplier': dynamic_outflow_state['outflow_multiplier'],
            'DynamicOutflow.emergency_release': dynamic_outflow_state['emergency_release'],
            'SpillwayController.outflow_multiplier': spillway_actions.get('outflow_multiplier', 1.0),
            'SpillwayController.emergency_release': spillway_actions.get('emergency_release', False),
            'LevelMonitor.output': level_monitor_agent.model.output if hasattr(level_monitor_agent.model, 'output') else current_level
        })
        
        # 每1000步打印一次状态
        if i % 1000 == 0:
            print(f"步长 {i}: 时间={host.current_time/3600:.1f}h, 水位={reservoir_agent.model.level:.3f}m, 库容={reservoir_agent.model.volume:.0f}m³")
            print(f"      调蓄状态: 出流倍数={spillway_actions.get('outflow_multiplier', 1.0)}, 紧急泄洪={spillway_actions.get('emergency_release', False)}")
            print(f"      动态出流: 当前出流={current_dynamic_outflow:.1f}m³/s, 倍数={dynamic_outflow_state['outflow_multiplier']:.1f}")

    # 6. 绘图
    results_df = pd.DataFrame(results)
    print("\n仿真结果 (前5行):")
    print(results_df.head())
    print("\n仿真结果 (后5行):")
    print(results_df.tail())
    
    # 计算水位变化
    initial_level = results_df['IrregularReservoir.level'].iloc[0]
    final_level = results_df['IrregularReservoir.level'].iloc[-1]
    max_level = results_df['IrregularReservoir.level'].max()
    min_level = results_df['IrregularReservoir.level'].min()
    
    print(f"\n水位变化分析:")
    print(f"- 初始水位: {initial_level:.3f} m")
    print(f"- 最终水位: {final_level:.3f} m")
    print(f"- 最高水位: {max_level:.3f} m")
    print(f"- 最低水位: {min_level:.3f} m")
    print(f"- 水位变化: {final_level - initial_level:.3f} m")

    # 创建4个子图
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 14))
    fig.suptitle('第十二章: 非线性水库智能调蓄系统', fontsize=20, fontweight='bold')

    # 图1：水位变化
    ax1.plot(results_df['time'] / 3600, results_df['IrregularReservoir.level'], 'b-', linewidth=3, label='水库水位')
    ax1.axhline(y=11.5, color='orange', linestyle='--', alpha=0.7, label='调蓄启动阈值 (11.5m)')
    ax1.axhline(y=12.0, color='red', linestyle='--', alpha=0.7, label='中等调蓄阈值 (12.0m)')
    ax1.axhline(y=12.5, color='darkred', linestyle='--', alpha=0.7, label='高调蓄阈值 (12.5m)')
    ax1.axhline(y=13.0, color='purple', linestyle='--', alpha=0.7, label='紧急泄洪阈值 (13.0m)')
    ax1.set_ylabel('水位 (m)', fontsize=16)
    ax1.set_title('水库水位随时间变化', fontsize=18, fontweight='bold')
    ax1.legend(fontsize=14)
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='both', which='major', labelsize=14)

    # 图2：库容变化
    ax2.plot(results_df['time'] / 3600, results_df['IrregularReservoir.volume'] / 1e5, 'g-', linewidth=3, label='水库库容')
    ax2.set_ylabel('库容 (×10^5 m^3)', fontsize=16)
    ax2.set_title('水库库容随时间变化', fontsize=18, fontweight='bold')
    ax2.legend(fontsize=14)
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='both', which='major', labelsize=14)

    # 图3：流量对比
    ax3.plot(results_df['time'] / 3600, results_df['FloodInflow.value'], 'c-', linewidth=3, label='入库流量')
    ax3.plot(results_df['time'] / 3600, -results_df['BaseOutflow.value'], 'r-', linewidth=3, label='基础出库流量')
    ax3.plot(results_df['time'] / 3600, -results_df['DynamicOutflow.value'], 'purple', linewidth=3, label='动态调蓄出流')
    ax3.axhline(y=0, color='k', linestyle='-', alpha=0.3)
    ax3.set_ylabel('流量 (m^3/s)', fontsize=16)
    ax3.set_title('入库和出库流量对比', fontsize=18, fontweight='bold')
    ax3.legend(fontsize=14)
    ax3.grid(True, alpha=0.3)
    ax3.tick_params(axis='both', which='major', labelsize=14)

    # 图4：智能调蓄状态
    ax4.plot(results_df['time'] / 3600, results_df['DynamicOutflow.multiplier'], 'purple', linewidth=3, label='动态出流倍数')
    ax4.axhline(y=1.0, color='k', linestyle='--', alpha=0.5, label='正常出流 (倍数=1.0)')
    ax4.set_ylabel('出流倍数', fontsize=16)
    ax4.set_xlabel('时间 (h)', fontsize=16)
    ax4.set_title('智能调蓄系统状态', fontsize=18, fontweight='bold')
    ax4.legend(fontsize=14)
    ax4.grid(True, alpha=0.3)
    ax4.tick_params(axis='both', which='major', labelsize=14)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

if __name__ == "__main__":
    run_simulation()
