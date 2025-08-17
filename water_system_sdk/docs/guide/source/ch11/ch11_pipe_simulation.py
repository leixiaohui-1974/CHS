import matplotlib.pyplot as plt
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
    results = {'time': [], 'flow': [], 'velocity': []}

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
        results['time'].append(i * dt)
        results['flow'].append(state['flow'])
        results['velocity'].append(state['velocity'])
    print("Simulation finished.")

    # 3. 绘图
    fig, ax1 = plt.subplots(figsize=(12, 7))
    fig.suptitle('第十一章: 有压管道启动过程仿真', fontsize=16)

    color = 'tab:blue'
    ax1.set_xlabel('时间 (秒)')
    ax1.set_ylabel('流量 (m³/s)', color=color)
    ax1.plot(results['time'], results['flow'], color=color)
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True)

    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('流速 (m/s)', color=color)
    ax2.plot(results['time'], results['velocity'], color=color, linestyle='--')
    ax2.tick_params(axis='y', labelcolor=color)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

if __name__ == "__main__":
    run_simulation()
