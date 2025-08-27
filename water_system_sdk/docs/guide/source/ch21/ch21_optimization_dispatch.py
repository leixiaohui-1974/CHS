import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
import pandas as pd

from chs_sdk.core.host import AgentKernel as Host
from chs_sdk.modules.modeling.storage_models import LinearTank
from chs_sdk.modules.modeling.valve_models import GenericValve
from chs_sdk.agents.message import Message
import sys
import os
# 使用本地的project_utils.py，不影响其他章节
from project_utils import ModelAgent, SimpleDispatchAgent, EnhancedPIDAgent

def run_simulation():
    """
    This script demonstrates a hierarchical control system where a high-level
    DispatchAgent sends a new command to a low-level PIDAgent mid-simulation.
    """
    host = Host()

    # 1. 创建物理层组件
    host.add_agent(
        agent_class=ModelAgent, agent_id='Tank1', 
        model_class=LinearTank, 
        area=1000.0, initial_level=5.0, max_level=20.0
    )
    host.add_agent(
        agent_class=ModelAgent, agent_id='Tank2', 
        model_class=LinearTank, 
        area=800.0, initial_level=5.0, max_level=20.0
    )
    host.add_agent(
        agent_class=ModelAgent, agent_id='Valve1',
        model_class=GenericValve, cv_curve=[0, 8.0]  # 增加Cv从2.0到8.0，使出流更大，PID控制更有效
    )
    host.add_agent(
        agent_class=ModelAgent, agent_id='Valve2',
        model_class=GenericValve, cv_curve=[0, 6.0]  # 增加Cv从1.6到6.0，使出流更大，PID控制更有效
    )

    # 2. 创建控制层组件 - 使用增强版PIDAgent
    host.add_agent(
        agent_class=EnhancedPIDAgent, agent_id='PID1', 
        Kp=-0.8, Ki=-0.1, Kd=-0.01, set_point=5.0,  # PID1初始目标水位：5.0米
        input_topic='Tank1/level', output_topic='cmd/valve1/command',
        output_min=0.0, output_max=1.0  # 修复：输出阀门开度（0=关闭，1=全开），让阀门模型计算实际流量
    )
    host.add_agent(
        agent_class=EnhancedPIDAgent, agent_id='PID2', 
        Kp=-0.8, Ki=-0.1, Kd=-0.01, set_point=6.0,  # PID2初始目标水位：6.0米，使用正数PID参数
        input_topic='Tank2/level', output_topic='cmd/valve2/command',
        output_min=0.0, output_max=1.0   # 修复：输出阀门开度（0=关闭，1=全开），让阀门模型计算实际流量
    )

    # 3. 创建中央调度中心
    dispatch_logic = {
        200: Message(
            topic="cmd/pid1/set_point",
            sender_id="CentralDispatch",
            payload={"value": 5.5}       # PID1目标水位：5.0 → 5.5
        ),
        300: Message(
            topic="cmd/pid2/set_point",
            sender_id="CentralDispatch",
            payload={"value": 6.5}       # PID2目标水位：6.0 → 6.5
        ),
        400: Message(
            topic="cmd/pid2/set_point",
            sender_id="CentralDispatch",
            payload={"value": 5.5}       # PID2目标水位：6.5 → 5.5
        )
    }
    host.add_agent(
        agent_class=SimpleDispatchAgent, agent_id='CentralDispatch',
        dispatch_logic=dispatch_logic
    )

    # 4. 建立连接关系
    # 水库订阅阀门流量作为出流控制
    host._agents['Tank1'].subscribe('Valve1/inflow', 'outflow')  # 修复：水箱订阅阀门的实际流量作为出流控制
    host._agents['Tank2'].subscribe('Valve2/inflow', 'outflow')  # 修复：水箱订阅阀门的实际流量作为出流控制
    
    # 阀门订阅PID控制命令
    host._agents['Valve1'].subscribe('cmd/valve1/command', 'command')
    host._agents['Valve2'].subscribe('cmd/valve2/command', 'command')

    # 5. 初始化所有agent
    print("开始初始化所有agents...")
    for agent_id, agent in host._agents.items():
        print(f"正在初始化 {agent_id}...")
        if hasattr(agent, 'setup'):
            print(f"调用 {agent_id}.setup() 方法")
            agent.setup()
        else:
            print(f"{agent_id} 没有setup方法")
    print("所有agents初始化完成！")

    # 6. 设置初始入流，使系统更平衡
    host._agents['Tank1'].input_values['inflow'] = 5.0  # 增大到5 m³/s 固定入流，使PID控制效果更明显
    host._agents['Tank2'].input_values['inflow'] = 4.0  # 增大到4 m³/s 固定入流，使PID控制效果更明显
    
    # 初始化出流为0（阀门关闭状态）
    host._agents['Tank1'].input_values['outflow'] = 1.0  # 初始出流为1
    host._agents['Tank2'].input_values['outflow'] = 1.0  # 初始出流为1

    # 6. 运行仿真
    print("开始运行仿真...")
    print("初始状态：PID1目标水位5米，PID2目标水位6米")
    print("第590步时：中央调度中心将PID2的目标水位从6米降低到3米")
    print("=" * 80)
    
    # 启动仿真内核
    host.start(time_step=1.0)
    
    # 记录仿真数据
    simulation_data = {
        'time': [],
        'tank1_level': [],
        'tank2_level': [],
        'pid1_output': [],
        'pid2_output': [],
        'pid1_setpoint': [],
        'pid2_setpoint': []
    }
    
    for step in range(600):  # 从第0步开始运行600步
        current_time = step * host.time_step
        
        # 专门检查调度中心活动
        if 195 <= step <= 205 or 295 <= step <= 305 or 395 <= step <= 405:
            print(f"\n🔥🔥🔥 === 第{step}步调试信息 === 🔥🔥🔥")
            print(f"当前时间: {current_time}")
            dispatch_agent = host._agents['CentralDispatch']
            pid1_agent = host._agents['PID1']
            pid2_agent = host._agents['PID2']
            print(f"CentralDispatch状态: {dispatch_agent.status}")
            print(f"CentralDispatch调度逻辑: {dispatch_agent.dispatch_logic}")
            print(f"PID1当前目标值: {pid1_agent.set_point}")
            print(f"PID2当前目标值: {pid2_agent.set_point}")
            if step == 200:
                print(f"🚨🚨🚨 这是第200步！PID1目标值更新为5.5米！🚨🚨🚨")
            elif step == 300:
                print(f"🚨🚨🚨 这是第300步！PID2目标值更新为6.5米！🚨🚨🚨")
            elif step == 400:
                print(f"🚨🚨🚨 这是第400步！PID2目标值更新为5.5米！🚨🚨🚨")
        
        # 记录数据
        simulation_data['time'].append(current_time)
        
        # 获取水库水位
        tank1 = host._agents['Tank1']
        tank2 = host._agents['Tank2']
        if hasattr(tank1.model, 'level'):
            simulation_data['tank1_level'].append(tank1.model.level)
        else:
            simulation_data['tank1_level'].append(10.0)
            
        if hasattr(tank2.model, 'level'):
            simulation_data['tank2_level'].append(tank2.model.level)
        else:
            simulation_data['tank2_level'].append(10.0)
        
        # 获取PID输出和设定值
        pid1 = host._agents['PID1']
        pid2 = host._agents['PID2']
        simulation_data['pid1_setpoint'].append(pid1.set_point)
        simulation_data['pid2_setpoint'].append(pid2.set_point)
        
        # 计算PID输出（模拟）
        if hasattr(pid1, '_current_value') and pid1.initialized:
            error1 = pid1.set_point - pid1._current_value
            output1 = pid1.Kp * error1
            simulation_data['pid1_output'].append(output1)
        else:
            simulation_data['pid1_output'].append(0.0)
            
        if hasattr(pid2, '_current_value') and pid2.initialized:
            error2 = pid2.set_point - pid2._current_value
            output2 = pid2.Kp * error2
            simulation_data['pid2_output'].append(output2)
        else:
            simulation_data['pid2_output'].append(0.0)
        
        # 执行仿真步骤
        host.tick()
        
        # 检查PID控制器状态
        if step % 10 == 0:  # 每10步检查一次
            pid1 = host._agents['PID1']
            pid2 = host._agents['PID2']
            tank1 = host._agents['Tank1']
            tank2 = host._agents['Tank2']
            
            # 获取水箱的入流和出流信息
            tank1_inflow = tank1.input_values.get('inflow', 0.0)
            tank2_inflow = tank2.input_values.get('inflow', 0.0)
            
            print(f"时间步 {step}: Tank1水位={simulation_data['tank1_level'][-1]:.3f}m (入流={tank1_inflow:.1f}), "
                  f"Tank2水位={simulation_data['tank2_level'][-1]:.3f}m (入流={tank2_inflow:.1f})")
            print(f"  PID1: 状态={pid1.status}, 初始化={pid1.initialized}, 当前值={pid1._current_value:.3f}, 目标={pid1.set_point:.1f}")
            print(f"  PID2: 状态={pid2.status}, 初始化={pid2.initialized}, 当前值={pid2._current_value:.3f}, 目标={pid2.set_point:.1f}")
        
        # 每100步打印一次状态
        if step % 100 == 0:
            print(f"时间步 {step}: Tank1水位={simulation_data['tank1_level'][-1]:.3f}m, "
                  f"Tank2水位={simulation_data['tank2_level'][-1]:.3f}m, "
                  f"PID1设定值={simulation_data['pid1_setpoint'][-1]:.1f}m, "
                  f"PID2设定值={simulation_data['pid2_setpoint'][-1]:.1f}m")

    print("=" * 80)
    print("仿真完成！")
    
    # 停止仿真内核
    host.stop()
    
    # 7. 绘制结果图表
    plot_results(simulation_data)

def plot_results(data):
    """绘制仿真结果图表"""
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
    
    # 中央调度命令（图2）
    ax1.plot(data['time'], data['pid1_setpoint'], 'b--', label='PID1设定值', linewidth=2)
    ax1.plot(data['time'], data['pid2_setpoint'], 'r--', label='PID2设定值', linewidth=2)
    ax1.set_xlabel('时间 (s)')
    ax1.set_ylabel('设定值 (m)')
    ax1.set_title('中央调度命令')
    ax1.legend()
    ax1.grid(True)
    
    # PID输出变化
    ax2.plot(data['time'], data['pid1_output'], 'b-', label='PID1输出', linewidth=2)
    ax2.plot(data['time'], data['pid2_output'], 'r-', label='PID2输出', linewidth=2)
    ax2.set_xlabel('时间 (s)')
    ax2.set_ylabel('控制输出')
    ax2.set_title('PID控制器输出变化')
    ax2.legend()
    ax2.grid(True)
    
    # 水位对比图
    ax3.plot(data['time'], data['tank1_level'], 'b-', label='Tank1', linewidth=2)
    ax3.plot(data['time'], data['tank2_level'], 'r-', label='Tank2', linewidth=2)
    ax3.axvline(x=200, color='blue', linestyle=':', alpha=0.7, label='PID1目标更新')
    ax3.axvline(x=300, color='red', linestyle=':', alpha=0.7, label='PID2目标更新(6.5)')
    ax3.axvline(x=400, color='red', linestyle=':', alpha=0.7, label='PID2目标更新(5.5)')
    ax3.set_xlabel('时间 (s)')
    ax3.set_ylabel('水位 (m)')
    ax3.set_title('水位响应与调度效果')
    ax3.legend()
    ax3.grid(True)
    
    # plt.tight_layout()
    # plt.savefig('ch21_centralized_dispatch_results.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # print("图表已保存为: ch21_centralized_dispatch_results.png")

if __name__ == "__main__":
    run_simulation()
