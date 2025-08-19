import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def analyze_results():
    """
    This script demonstrates how to post-process simulation results
    to calculate Key Performance Indicators (KPIs) and create an
    annotated summary plot.
    """
    # 1. 加载仿真结果
    # 在真实项目中，这会是一个真实的文件路径。
    # 为使本例可独立运行，我们在这里“伪造”一个仿真结果DataFrame。
    # 这个数据是基于第六章的场景生成的。
    print("正在生成模拟的仿真结果数据...")
    time_steps = 1000
    dt = 1.0 # s
    time = np.arange(0, time_steps, dt)
    setpoint = 10.0
    # 模拟一个二阶系统的响应 + 噪声
    level_true = setpoint - 5 * np.exp(-0.01 * time) * np.cos(0.01 * time)
    level_sensed = level_true + np.random.normal(0, 0.1, time_steps)
    gate_flow = 8.0 + 2.0 * np.exp(-0.005 * time)

    results_df = pd.DataFrame({
        'time': time,
        'MainReservoir.level': level_sensed,
        'InletGate.flow': gate_flow
    })
    print("数据加载完毕。")

    # 2. 计算控制性能KPI
    print("\n--- 计算控制性能KPI ---")
    level = results_df['MainReservoir.level']

    # 稳态误差: 取最后10%时间的平均值与设定值的差
    steady_state_period = results_df.iloc[int(len(results_df) * 0.9):]
    ss_error = abs(steady_state_period['MainReservoir.level'].mean() - setpoint)
    print(f"稳态误差: {ss_error:.3f} m")

    # 超调量
    peak_level = level.max()
    overshoot = ((peak_level - setpoint) / setpoint) * 100 if setpoint > 0 else 0
    overshoot = max(0, overshoot)
    print(f"超调量: {overshoot:.2f} %")

    # 3. 计算业务KPI
    print("\n--- 计算业务KPI ---")
    # 总泄流量 (m³): 流量(m³/s) * 时间步长(s)
    total_volume_discharged = results_df['InletGate.flow'].sum() * dt
    print(f"总泄流量: {total_volume_discharged / 1e6:.3f} 百万立方米")

    # 4. 创建带有KPI标注的图表
    print("\n正在生成分析图表...")
    fig, ax1 = plt.subplots(figsize=(15, 8))
    fig.suptitle('第二十二章: 仿真结果后处理与KPI分析', fontsize=16)

    ax1.plot(results_df['time'], results_df['MainReservoir.level'], 'b-', label='水库水位')
    ax1.axhline(y=setpoint, color='r', linestyle='--', label=f'目标水位 ({setpoint}m)')
    ax1.axhline(y=peak_level, color='orange', linestyle=':', label=f'峰值水位 ({peak_level:.2f}m)')

    ax1.set_xlabel('时间 (秒)')
    ax1.set_ylabel('水位 (m)')
    ax1.legend(loc='lower right')
    ax1.grid(True)

    # 在图表上添加文本标注
    kpi_text = (
        f"KPIs:\n"
        f"稳态误差: {ss_error:.3f} m\n"
        f"超调量: {overshoot:.2f} %\n"
        f"总泄流量: {total_volume_discharged / 1e6:.3f} MCM"
    )
    ax1.text(0.65, 0.35, kpi_text, transform=ax1.transAxes,
             fontsize=12, verticalalignment='top',
             bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5))

    plt.show()


if __name__ == "__main__":
    analyze_results()
