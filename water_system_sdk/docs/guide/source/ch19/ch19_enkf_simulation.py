import numpy as np
import matplotlib.pyplot as plt

# This is a simple way to make the SDK accessible to the script.
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from chs_sdk.modules.control.data_assimilation import EnsembleKalmanFilter

def run_enkf_simulation():
    """
    This script demonstrates how to use the Ensemble Kalman Filter (EnKF)
    to track the state of a simple non-linear system.
    """
    # 1. 定义“真实”系统和仿真参数
    num_steps = 100
    true_x = np.zeros(num_steps)
    true_y = np.zeros(num_steps)

    # 真实的状态 x 是一个简单的斜坡函数
    for i in range(1, num_steps):
        true_x[i] = true_x[i-1] + 0.1

    # 真实的观测 y 是 x 的平方
    true_y = true_x**2

    # 2. 配置EnKF
    # 我们的状态只有一个变量 x
    state_size = 1
    # 集合成员数量
    n_ensemble = 50

    # 状态转移函数 f(x): x_k = x_{k-1} + 0.1
    # 这是一个简单的线性函数，但观测函数是非线性的
    def state_transition_func(x_ensemble):
        # The function must operate on the entire ensemble (N_ensemble x N_state)
        return x_ensemble + 0.1

    # 观测函数 h(x): y = x^2
    def observation_func(x_ensemble):
        # The function must operate on the entire ensemble
        return x_ensemble**2

    # 过程噪声Q: 模型有多不准
    Q = np.diag([0.01**2])
    # 测量噪声R: 传感器有多不准
    measurement_noise_std = 0.2
    R = np.diag([measurement_noise_std**2])

    # 初始状态和协方差
    x0 = np.array([0.0])
    P0 = np.diag([0.5**2])

    enkf = EnsembleKalmanFilter(
        f=state_transition_func,
        h=observation_func,
        Q=Q, R=R, x0=x0, P0=P0,
        n_ensemble=n_ensemble
    )

    # 3. 仿真循环
    results = {'time': [], 'true_x': [], 'estimated_x': [], 'measurement_y': []}

    print("Running Ensemble Kalman Filter simulation...")
    for i in range(num_steps):
        # 预测
        enkf.predict()

        # 生成带噪声的测量
        measurement = true_y[i] + np.random.normal(0, measurement_noise_std)

        # 更新
        enkf.update(np.array([measurement]))

        # 记录结果
        estimated_x = enkf.get_state()
        results['time'].append(i)
        results['true_x'].append(true_x[i])
        results['estimated_x'].append(estimated_x[0])
        results['measurement_y'].append(measurement)
    print("Simulation finished.")

    # 4. 绘图
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    fig.suptitle('第十九章: EnKF在非线性系统中的状态追踪', fontsize=16)

    # 图1：状态x的追踪效果
    ax1.plot(results['time'], results['true_x'], 'b-', linewidth=3, label='真实状态 (x)')
    ax1.plot(results['time'], results['estimated_x'], 'g--', linewidth=2, label='EnKF 估计状态 (x)')
    ax1.set_ylabel('状态 x')
    ax1.legend()
    ax1.grid(True)

    # 图2：观测空间y的对比
    ax2.plot(results['time'], true_y, 'b-', linewidth=3, label='真实观测 (y = x²)')
    ax2.plot(results['time'], results['measurement_y'], 'ko', markersize=2, alpha=0.4, label='带噪声的测量值 (y)')
    ax2.set_xlabel('时间步')
    ax2.set_ylabel('观测 y')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()


if __name__ == "__main__":
    run_enkf_simulation()
