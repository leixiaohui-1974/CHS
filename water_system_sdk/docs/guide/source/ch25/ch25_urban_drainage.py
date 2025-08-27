import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
import numpy as np
import pandas as pd

from chs_sdk.core.host import AgentKernel as Host
from chs_sdk.modules.modeling.control_structure_models import PumpStationModel
from chs_sdk.modules.disturbances.timeseries_disturbance import TimeSeriesDisturbance
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from fixed_project_utils import FixedModelAgent, EnhancedLinearTank

def run_simulation():
    """
    This script simulates an urban drainage system, where a pump station
    is activated to prevent a detention pond from overflowing during a
    heavy storm event.
    """
    host = Host()

    # 1. 定义降雨事件 (mm/hr)
    rainfall_times = np.array([0, 1, 2, 3, 4, 5, 6]) * 3600
    rainfall_intensity = [0, 10, 50, 30, 15, 5, 0]
    host.add_agent(
        agent_class=FixedModelAgent,
        agent_id='Rainfall',
        model_class=TimeSeriesDisturbance,
        times=rainfall_times,
        values=rainfall_intensity)

    # 2. 创建物理组件 - 使用修复版本的LinearTank
    host.add_agent(
        agent_class=FixedModelAgent,
        agent_id='DetentionPond',
        model_class=EnhancedLinearTank,
        area=1e5,
        initial_level=2.0,
        max_level=5.0)
    host.add_agent(
        agent_class=FixedModelAgent,
        agent_id='DrainagePump',
        model_class=PumpStationModel,
        num_pumps_total=3,
        curve_coeffs=[-0.001, 0.02, 25])

    # 3. 建立连接
    rainfall_agent = host._agents['Rainfall']
    pond_agent = host._agents['DetentionPond']
    pump_agent = host._agents['DrainagePump']

    pond_agent.subscribe(f"{pump_agent.agent_id}/output", 'release_outflow')

    # 4. 仿真循环与控制逻辑
    num_steps = 12 * 60
    dt = 60.0
    pump_on_count = 0
    results = []
    catchment_area_km2 = 10.0
    runoff_coeff = 0.6

    host.start(time_step=dt)

    for i in range(num_steps):
        current_rainfall_mmhr = rainfall_agent.model.output
        runoff_m3s = current_rainfall_mmhr / 1000 / 3600 * (catchment_area_km2 * 1e6) * runoff_coeff
        pond_agent.input_values['inflow'] = runoff_m3s

        pond_level = pond_agent.model.output
        if pond_level > 4.5:
            pump_on_count = 3
        elif pond_level < 2.5:
            pump_on_count = 0

        pump_agent.input_values['num_pumps_on'] = pump_on_count
        pump_agent.input_values['inlet_pressure'] = pond_level
        pump_agent.input_values['outlet_pressure'] = 3.0

        # 调试信息：查看关键变量
        if i % 60 == 0:  # 每小时输出一次调试信息
            print(f"\n=== 时间步 {i} (第{i/60:.1f}小时) ===")
            print(f"降雨强度: {current_rainfall_mmhr:.1f} mm/hr")
            print(f"径流量: {runoff_m3s:.2f} m³/s")
            print(f"调蓄池水位: {pond_level:.3f} m")
            print(f"泵站状态: {pump_on_count}台泵运行")
            print(f"调蓄池入流参数: {pond_agent.input_values.get('inflow', 0):.2f} m³/s")
            print(f"调蓄池出流参数: {pond_agent.input_values.get('release_outflow', 0):.2f} m³/s")
            
        host.tick()
        
        # 步进后获取更新的值
        pump_flow = pump_agent.model.output
        
        # 更多调试信息
        if i % 60 == 0:
            print(f"泵站实际流量: {pump_flow:.2f} m³/s")
            print(f"调蓄池更新后水位: {pond_agent.model.output:.3f} m")

        results.append({
            'time': host.current_time,
            'DetentionPond.level': pond_level,
            'DrainagePump.flow': pump_agent.model.output,
            'pump_status': pump_on_count,
            'rainfall': current_rainfall_mmhr
        })

    # 5. 绘图
    results_df = pd.DataFrame(results)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    fig.suptitle('第二十五章: 城市排水防涝仿真', fontsize=16)

    ax1.plot(results_df['time'] / 60, results_df['DetentionPond.level'], 'b-', label='调蓄池水位')
    ax1.axhline(y=4.5, color='r', linestyle='--', label='泵站启动水位')
    ax1.axhline(y=2.5, color='g', linestyle='--', label='泵站关闭水位')
    ax1.set_ylabel('水位 (m)'); ax1.legend(); ax1.grid(True)

    ax2.bar(results_df['time'] / 60, results_df['rainfall'], width=1.0, color='c', alpha=0.5, label='降雨强度 (mm/hr)')
    ax2.set_ylabel('降雨强度', color='c'); ax2.tick_params(axis='y', labelcolor='c')
    ax2.legend(loc='upper left')

    ax2b = ax2.twinx()
    ax2b.plot(results_df['time'] / 60, results_df['DrainagePump.flow'], 'm--', label='泵站排出流量 (m^3/s)')
    ax2b.set_ylabel('流量', color='m'); ax2b.tick_params(axis='y', labelcolor='m')
    ax2b.legend(loc='upper right')
    ax2.set_xlabel('时间 (分钟)')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # # 保存图形到文件
    # plt.savefig('ch25_urban_drainage_results.png', dpi=300, bbox_inches='tight')
    # print("\n=== 仿真结果图表已保存为 ch25_urban_drainage_results.png ===")
    
    # 显示图形（如果在GUI环境中）
    try:
        plt.show()
    except Exception as e:
        print(f"无法显示图形: {e}")
    
    # 打印仿真统计信息
    print("\n=== 城市调蓄池排涝联动仿真统计 ===")
    print(f"仿真时长: {num_steps} 分钟 ({num_steps/60:.1f} 小时)")
    print(f"汇水区面积: {catchment_area_km2} 平方公里")
    print(f"径流系数: {runoff_coeff}")
    
    max_rainfall = max(results_df['rainfall'])
    max_pond_level = max(results_df['DetentionPond.level'])
    max_pump_flow = max(results_df['DrainagePump.flow'])
    
    print(f"\n=== 关键指标 ===")
    print(f"最大降雨强度: {max_rainfall:.1f} mm/hr")
    print(f"调蓄池最高水位: {max_pond_level:.2f} m")
    print(f"最大泵站流量: {max_pump_flow:.1f} m³/s")
    
    # 计算泵站运行时间
    pump_running_steps = sum(1 for status in results_df['pump_status'] if status > 0)
    pump_running_time = pump_running_steps * dt / 60  # 转换为分钟
    print(f"泵站运行时间: {pump_running_time:.1f} 分钟 ({pump_running_time/60:.1f} 小时)")
    
    # 检查是否达标
    pond_max_safe_level = 5.0  # 假设最大安全水位为5米
    if max_pond_level <= pond_max_safe_level:
        print(f"\n✅ 达标测试通过！调蓄池最高水位 {max_pond_level:.2f}m 未超过安全水位 {pond_max_safe_level}m")
    else:
        print(f"\n❌ 达标测试失败！调蓄池最高水位 {max_pond_level:.2f}m 超过了安全水位 {pond_max_safe_level}m")
        
    return results_df


if __name__ == "__main__":
    run_simulation()
