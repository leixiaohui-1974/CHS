import sys
import os
# 添加必要的路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'water_system_sdk', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'water_system_sdk', 'docs', 'guide', 'source'))

import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
import numpy as np
import pandas as pd

class SimpleTank:
    """简化的水箱模型，确保数值积分的正确性"""
    def __init__(self, initial_level=50.0, area=1000.0):
        self.level = initial_level
        self.area = area
        self.volume = initial_level * area
        self.inflow = 0.0
        self.outflow = 0.0
        
    def step(self, dt, inflow=0.0, outflow=0.0):
        """数值积分更新水位"""
        self.inflow = inflow
        self.outflow = outflow
        
        # 净流量
        net_flow = inflow - outflow
        
        # 体积变化
        dvolume = net_flow * dt
        self.volume += dvolume
        
        # 水位更新
        self.level = max(0.0, self.volume / self.area)
        
        return self.level

class SimplePump:
    """简化的泵站模型"""
    def __init__(self, max_flow=80.0):
        self.max_flow = max_flow
        self.is_on = False
        self.flow = 0.0
        
    def step(self, pump_on, inlet_pressure, outlet_pressure):
        """根据泵的状态和压力差计算流量"""
        self.is_on = pump_on
        
        if pump_on:
            # 简化的泵特性曲线：流量与压力差有关
            pressure_diff = max(0, inlet_pressure - outlet_pressure)
            self.flow = min(self.max_flow, self.max_flow * (1 + pressure_diff / 100.0))
        else:
            self.flow = 0.0
            
        return self.flow

def run_improved_simulation():
    """改进的城市供水系统仿真"""
    print("开始运行改进的城市供水系统仿真...")
    
    # 1. 创建组件
    print("创建系统组件...")
    source_tank = SimpleTank(initial_level=10.0, area=1e5)  # 大水源
    elevated_tank = SimpleTank(initial_level=54.0, area=1000.0)  # 高架水箱
    pump = SimplePump(max_flow=20.0)  # 调整泵的最大流量
    
    # 2. 仿真参数
    total_time = 24 * 3600  # 24小时
    dt = 60.0  # 1分钟步长
    num_steps = int(total_time / dt)
    
    # 3. 控制参数
    level_low = 52.0   # 开泵水位
    level_high = 58.0  # 停泵水位
    pump_on = False
    
    # 4. 数据记录
    results = []
    
    print("开始仿真循环...")
    for i in range(num_steps):
        current_time = i * dt
        
        # 城市需水量（时变）
        hour = current_time / 3600.0
        demand = 8 + 4 * np.sin(2 * np.pi * hour / 24.0)  # 4-12 m³/s
        
        # 控制逻辑
        tank_level = elevated_tank.level
        
        if tank_level < level_low:
            if not pump_on:
                print(f"时间 {hour:.1f}h: 水位降至{tank_level:.2f}m，启动水泵")
            pump_on = True
        elif tank_level > level_high:
            if pump_on:
                print(f"时间 {hour:.1f}h: 水位升至{tank_level:.2f}m，关闭水泵")
            pump_on = False
        
        # 泵站运行
        pump_flow = pump.step(pump_on, source_tank.level, elevated_tank.level)
        
        # 更新水箱状态
        source_tank.step(dt, inflow=0, outflow=pump_flow)
        elevated_tank.step(dt, inflow=pump_flow, outflow=demand)
        
        # 记录数据
        results.append({
            'time': current_time,
            'hour': hour,
            'elevated_level': elevated_tank.level,
            'source_level': source_tank.level,
            'pump_on': pump_on,
            'pump_flow': pump_flow,
            'demand': demand,
            'net_flow': pump_flow - demand
        })
        
        # 每小时输出状态
        if i % 60 == 0:
            print(f"时间: {hour:.1f}h, 高架水箱: {elevated_tank.level:.2f}m, "
                  f"泵状态: {'开启' if pump_on else '关闭'}, "
                  f"泵流量: {pump_flow:.1f}m³/s, 需水量: {demand:.1f}m³/s")
    
    print("仿真完成，生成分析结果...")
    
    # 5. 结果分析
    results_df = pd.DataFrame(results)
    
    # 绘图
    fig, axes = plt.subplots(3, 1, figsize=(15, 12), sharex=True)
    fig.suptitle('改进的城市供水系统仿真结果', fontsize=16)
    
    # 子图1：水位变化
    ax1 = axes[0]
    ax1.plot(results_df['hour'], results_df['elevated_level'], 'b-', linewidth=2, label='高架水箱水位')
    ax1.axhline(y=level_high, color='r', linestyle='--', alpha=0.7, label=f'停泵水位 ({level_high}m)')
    ax1.axhline(y=level_low, color='g', linestyle='--', alpha=0.7, label=f'启泵水位 ({level_low}m)')
    ax1.set_ylabel('水位 (m)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_title('水位控制效果')
    
    # 子图2：泵状态和流量
    ax2 = axes[1]
    ax2.plot(results_df['hour'], results_df['pump_on'].astype(int), 'm-', 
             drawstyle='steps-post', linewidth=2, label='泵状态 (开/关)')
    ax2_twin = ax2.twinx()
    ax2_twin.plot(results_df['hour'], results_df['pump_flow'], 'orange', 
                  alpha=0.8, label='泵流量')
    ax2.set_ylabel('泵状态')
    ax2_twin.set_ylabel('流量 (m³/s)')
    ax2.legend(loc='upper left')
    ax2_twin.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    ax2.set_title('泵站运行状态')
    
    # 子图3：需水量和净流量
    ax3 = axes[2]
    ax3.plot(results_df['hour'], results_df['demand'], 'c:', linewidth=2, label='城市需水量')
    ax3.plot(results_df['hour'], results_df['net_flow'], 'purple', alpha=0.7, label='净流量 (流入-流出)')
    ax3.axhline(y=0, color='k', linestyle='-', alpha=0.5)
    ax3.set_ylabel('流量 (m³/s)')
    ax3.set_xlabel('时间 (小时)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_title('流量平衡')
    
    # plt.tight_layout()
    # plt.savefig('improved_water_supply_simulation.png', dpi=300, bbox_inches='tight')
    # print("结果图表已保存为 improved_water_supply_simulation.png")
    plt.show()
    
    # 6. 性能分析
    print("\n=== 仿真结果分析 ===")
    
    level_data = results_df['elevated_level']
    pump_switches = (results_df['pump_on'].astype(int).diff() == 1).sum()
    pump_runtime = results_df['pump_on'].sum() / len(results_df) * 24
    
    print(f"高架水箱水位范围: {level_data.min():.2f}m - {level_data.max():.2f}m")
    print(f"水泵启动次数: {pump_switches}次")
    print(f"水泵运行时间: {pump_runtime:.1f}小时 ({pump_runtime/24*100:.1f}%)")
    print(f"平均需水量: {results_df['demand'].mean():.2f}m³/s")
    print(f"平均泵流量: {results_df['pump_flow'].mean():.2f}m³/s")
    
    # 控制性能评估
    level_in_range = ((level_data >= level_low-2) & (level_data <= level_high+2)).mean()
    level_variance = level_data.var()
    
    print(f"水位控制精度: {level_in_range*100:.1f}% 的时间在目标范围内")
    print(f"水位波动方差: {level_variance:.3f}")
    
    # 判断控制效果
    if level_data.min() >= 50 and level_data.max() <= 60 and pump_switches > 0:
        print("✅ 控制系统达标：水位保持在合理范围，泵站正常切换")
        success = True
    else:
        print("⚠️ 控制系统需要调优")
        success = False
        
    if pump_switches == 0:
        print("❌ 泵站控制逻辑未生效")
    elif pump_switches > 20:
        print("⚠️ 泵站切换过于频繁，可能需要增加滞后")
    else:
        print(f"✅ 泵站切换频率合理 ({pump_switches}次/24h)")
    
    return success, results_df

if __name__ == "__main__":
    try:
        success, data = run_improved_simulation()
        
        if success:
            print("\n🎯 供水系统仿真成功达标！")
        else:
            print("\n⚠️ 系统需要进一步优化")
            
    except Exception as e:
        print(f"运行出错: {e}")
        import traceback
        traceback.print_exc()