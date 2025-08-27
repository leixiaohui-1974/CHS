import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
import sys
import os

# 添加正确的模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))
from chs_sdk.modules.modeling.pipeline_model import PipelineModel

def run_simulation():
    """
    This script demonstrates the startup dynamics of a pressurized pipeline,
    showing how flow accelerates and stabilizes due to pressure and friction.
    """
    # 1. 初始化管道模型
    pipe = PipelineModel(
        name='MainPipe',
        length=1000.0,      # 1000米长
        diameter=0.5,       # 0.5米管径
        method='darcy_weisbach',
        friction_factor=0.025 # 摩擦系数
    )

    # 2. 仿真参数与边界条件
    dt = 1.0  # 时间步长为1秒
    num_steps = 300 # 模拟300秒
    inlet_pressure = 50.0  # 上游压力（水位）
    outlet_pressure = 40.0 # 下游压力（水位）

    # 存储结果用于绘图
    results = {
        'time': [], 
        'flow': [], 
        'velocity': [],
        'pressure_diff': [],      # 新增：压力差
        'friction_loss': [],      # 新增：摩擦损失
        'net_driving_force': []   # 新增：净驱动力
    }

    print("Running pipeline simulation...")
    for i in range(num_steps):
        # 运行一个步长
        pipe.step(
            inlet_pressure=inlet_pressure,
            outlet_pressure=outlet_pressure,
            dt=dt
        )

        # 记录结果
        state = pipe.get_state()
        current_velocity = state['velocity']
        
        # 计算压力差和摩擦损失
        pressure_diff = inlet_pressure - outlet_pressure  # 固定10米
        friction_loss = pipe._calculate_head_loss(current_velocity)  # 随流速变化
        net_force = pressure_diff - friction_loss  # 净驱动力
        
        results['time'].append(i * dt)
        results['flow'].append(state['flow'])
        results['velocity'].append(current_velocity)
        results['pressure_diff'].append(pressure_diff)
        results['friction_loss'].append(friction_loss)
        results['net_driving_force'].append(net_force)
    print("Simulation finished.")

    # 3. 绘图 - 2x2布局
    fig = plt.figure(figsize=(16, 12))
    fig.suptitle('第十一章: 有压管道启动过程仿真', fontsize=18, fontweight='bold')

    # 图1: 流量和流速随时间变化
    ax1 = plt.subplot(2, 2, 1)
    color1 = 'tab:blue'
    ax1.set_xlabel('时间 (s)', fontsize=12)
    ax1.set_ylabel('流量 (m^3/s)', color=color1, fontsize=12)
    ax1.plot(results['time'], results['flow'], color=color1, linewidth=2, label='流量')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, alpha=0.3)
    ax1.set_title('图1: 流量和流速随时间变化', fontsize=14, fontweight='bold')
    
    ax1_twin = ax1.twinx()
    color2 = 'tab:red'
    ax1_twin.set_ylabel('流速 (m/s)', color=color2, fontsize=12)
    ax1_twin.plot(results['time'], results['velocity'], color=color2, linestyle='--', linewidth=2, label='流速')
    ax1_twin.tick_params(axis='y', labelcolor=color2)
    
    # 添加图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1_twin.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='lower right', fontsize=10)

    # 图2: 压力差和摩擦损失随时间变化
    ax2 = plt.subplot(2, 2, 2)
    ax2.plot(results['time'], results['pressure_diff'], 'g-', linewidth=2, label='压力差')
    ax2.plot(results['time'], results['friction_loss'], 'r-', linewidth=2, label='摩擦损失')
    ax2.plot(results['time'], results['net_driving_force'], 'b--', linewidth=2, label='净驱动力')
    ax2.axhline(y=0, color='k', linestyle=':', alpha=0.7, label='平衡线')
    ax2.set_xlabel('时间 (s)', fontsize=12)
    ax2.set_ylabel('水头 (m)', fontsize=12)
    ax2.set_title('图2: 压力差和摩擦损失随时间变化', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)

    # 图3: 净驱动力详细分析
    ax3 = plt.subplot(2, 2, 3)
    ax3.plot(results['time'], results['net_driving_force'], 'b-', linewidth=2, label='净驱动力')
    ax3.axhline(y=0, color='r', linestyle='--', alpha=0.8, label='稳定状态')
    ax3.fill_between(results['time'], results['net_driving_force'], alpha=0.3, color='blue')
    ax3.set_xlabel('时间 (s)', fontsize=12)
    ax3.set_ylabel('净驱动力 (m)', fontsize=12)
    ax3.set_title('图3: 净驱动力变化（趋于0时达到稳定）', fontsize=14, fontweight='bold')
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3)

    # 图4: 流量-摩擦损失关系图
    ax4 = plt.subplot(2, 2, 4)
    # 绘制仿真轨迹
    ax4.plot(results['flow'], results['friction_loss'], 'bo-', markersize=3, linewidth=1, alpha=0.7, label='仿真轨迹')
    
    # 绘制理论曲线
    import numpy as np
    flow_theory = np.linspace(0, max(results['flow'])*1.2, 100)
    velocity_theory = flow_theory / pipe.area
    friction_theory = [pipe._calculate_head_loss(v) for v in velocity_theory]
    ax4.plot(flow_theory, friction_theory, 'r-', linewidth=2, label='理论曲线')
    
    # 标记平衡点
    final_flow = results['flow'][-1]
    final_friction = results['friction_loss'][-1]
    ax4.plot(final_flow, final_friction, 'ro', markersize=8, label=f'稳定点({final_flow:.3f}, {final_friction:.1f})')
    
    # 标记压力差线
    ax4.axhline(y=10, color='g', linestyle='--', linewidth=2, label='可用压力差(10m)')
    
    ax4.set_xlabel('流量 (m^3/s)', fontsize=12)
    ax4.set_ylabel('摩擦损失 (m)', fontsize=12)
    ax4.set_title('图4: 流量-摩擦损失关系图', fontsize=14, fontweight='bold')
    ax4.legend(fontsize=10)
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_simulation()
