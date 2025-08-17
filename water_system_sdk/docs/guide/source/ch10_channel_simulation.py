import matplotlib.pyplot as plt
import numpy as np
from chs_sdk.modules.modeling.st_venant_model import StVenantModel

def run_simulation():
    """
    This script demonstrates how to use the StVenantModel to simulate
    the propagation of a flood wave down an open channel.
    """
    # 1. 定义网络拓扑
    # 节点定义
    nodes_config = [
        {'name': 'Upstream', 'type': 'inflow', 'bed_elevation': 10.0},
        {'name': 'Downstream', 'type': 'level', 'bed_elevation': 5.0, 'initial_level': 7.0}
    ]

    # 河段定义
    reaches_config = [
        {
            'name': 'MainChannel',
            'from_node': 'Upstream',
            'to_node': 'Downstream',
            'length': 5000,         # 5公里长
            'num_cells': 25,        # 将河段离散为25个计算单元
            'cross_section': {
                'type': 'trapezoidal',
                'bottom_width': 20.0,
                'side_slope': 2.0     # 边坡系数m=2 (2H:1V)
            },
            'roughness': 0.035      # 曼宁糙率系数
        }
    ]

    # 2. 初始化 StVenantModel
    model = StVenantModel(nodes_data=nodes_config, reaches_data=reaches_config)

    # 3. 运行仿真
    dt = 60.0  # 时间步长为60秒
    num_steps = 180 # 模拟180分钟 (3小时)

    # 存储结果用于绘图
    results = {
        'time': [],
        'upstream_flow': [],
        'downstream_flow': [],
        'midpoint_level': []
    }

    print("Running simulation...")
    for i in range(num_steps):
        # 构造一个洪水波作为上游入流边界
        # 流量在60分钟时达到峰值
        time_minutes = i * dt / 60
        inflow = 10 + 40 * np.exp(-((time_minutes - 60)**2) / (2 * 20**2))

        # 更新上游边界条件
        model.set_boundary_condition('Upstream', 'inflow', inflow)

        # 运行一个步长
        model.step(dt)

        # 记录结果
        state = model.get_state()
        results['time'].append(i * dt / 60) # 时间单位：分钟
        results['upstream_flow'].append(state['reaches']['MainChannel']['inflow'])
        results['downstream_flow'].append(state['reaches']['MainChannel']['outflow'])

        # 获取河道中点（第12个单元）的水位
        midpoint_level = state['reaches']['MainChannel']['water_levels'][12]
        results['midpoint_level'].append(midpoint_level)
    print("Simulation finished.")

    # 4. 绘图
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    fig.suptitle('第十章: 圣维南模型洪水波演进仿真', fontsize=16)

    # 图1：流量过程线
    ax1.plot(results['time'], results['upstream_flow'], 'b-', label='上游流量')
    ax1.plot(results['time'], results['downstream_flow'], 'r--', label='下游流量')
    ax1.set_ylabel('流量 (m³/s)')
    ax1.legend()
    ax1.grid(True)

    # 图2：中点水位过程线
    ax2.plot(results['time'], results['midpoint_level'], 'g-', label='河道中点水位')
    ax2.set_ylabel('水位 (m)')
    ax2.set_xlabel('时间 (分钟)')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

if __name__ == "__main__":
    run_simulation()
