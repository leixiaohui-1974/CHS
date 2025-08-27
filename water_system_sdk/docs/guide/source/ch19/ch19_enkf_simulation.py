import sys
import os

# 添加水系统SDK源码路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../src')))

import numpy as np
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

from chs_sdk.modules.control.data_assimilation import EnsembleKalmanFilter

def run_enkf_simulation():
    """
    This script demonstrates how to use the Ensemble Kalman Filter (EnKF)
    to track the state of a simple non-linear system.
    """
    # 1. 定义"真实"系统和仿真参数
    num_steps = 100
    true_x = np.zeros(num_steps)
    true_y = np.zeros(num_steps)

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
    print("=" * 60)
    print("时间步 | 真实状态x | 真实观测y | 测量值y+noise | EnKF估计x | 误差")
    print("=" * 60)
    
    for i in range(num_steps):
        # 1. 传播真实状态（模拟真实系统）
        if i > 0:
            true_x[i] = true_x[i-1] + 0.1  # 真实状态传播
        
        # 2. 基于真实状态生成观测
        true_y[i] = true_x[i]**2  # 真实观测
        measurement = true_y[i] + np.random.normal(0, measurement_noise_std)
        
        # 3. EnKF预测
        enkf.predict()
        
        # 4. EnKF更新
        enkf.update(np.array([measurement]))
        
        # 5. 记录结果
        estimated_x = enkf.get_state()
        results['time'].append(i)
        results['true_x'].append(true_x[i])
        results['estimated_x'].append(estimated_x[0])
        results['measurement_y'].append(measurement)
        
        # 6. 输出中间参数（每10步输出一次，避免输出过多）
        if i % 10 == 0 or i < 5 or i > num_steps - 5:
            error = abs(true_x[i] - estimated_x[0])
            print(f"{i:6d} | {true_x[i]:9.3f} | {true_y[i]:9.3f} | {measurement:12.3f} | {estimated_x[0]:9.3f} | {error:6.3f}")
    
    print("=" * 60)
    print("Simulation finished.")
    
    # 输出最终统计信息
    print("\n" + "=" * 60)
    print("仿真结果统计")
    print("=" * 60)
    print(f"仿真时长: {num_steps} 步")
    print(f"真实状态范围: {true_x[0]:.3f} → {true_x[-1]:.3f}")
    print(f"观测值范围: {true_y[0]:.3f} → {true_y[-1]:.3f}")
    print(f"测量噪声标准差: {measurement_noise_std:.3f}")
    
    # 计算估计误差统计
    errors = [abs(tx - ex) for tx, ex in zip(results['true_x'], results['estimated_x'])]
    print(f"平均绝对误差: {np.mean(errors):.4f}")
    print(f"最大绝对误差: {np.max(errors):.4f}")
    print(f"误差标准差: {np.std(errors):.4f}")
    print("=" * 60)

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
    ax2.plot(results['time'], true_y, 'b-', linewidth=3, label='真实观测 (y = x^2)')
    ax2.plot(results['time'], results['measurement_y'], 'ko', markersize=2, alpha=0.4, label='带噪声的测量值 (y)')
    ax2.set_xlabel('时间步')
    ax2.set_ylabel('观测 y')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()
    # output_dir = 'results/ch19'
    # os.makedirs(output_dir, exist_ok=True)
    # output_path = os.path.join(output_dir, 'ch19_enkf_simulation.png')
    # plt.savefig(output_path)
    # plt.close()
    # print(f"Plot saved to {output_path}")


if __name__ == "__main__":
    run_enkf_simulation()
