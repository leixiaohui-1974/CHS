import numpy as np
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

from chs_sdk.modules.modeling.storage_models import LinearTank
from chs_sdk.modules.control.kalman_filter import KalmanFilter

def run_kalman_filter_simulation():
    """
    This script demonstrates how a Kalman Filter can fuse a simple, imperfect
    model with noisy measurements to produce a high-fidelity state estimate.
    """
    # 1. 设置“真实世界”和“不完美模型”
    dt = 60.0 # 60秒步长
    true_model = LinearTank(area=1000.0, initial_level=5.0)
    # 我们的仿真模型，参数不准
    open_loop_model = LinearTank(area=800.0, initial_level=5.0)
    # 将被KF修正的模型
    kf_model = LinearTank(area=800.0, initial_level=5.0)

    # 2. 配置卡尔曼滤波器
    # 对于水库模型: level_t = level_{t-1} + (inflow/area)*dt
    # 这是一个线性系统: x_k = F*x_{k-1} + B*u_k
    # 我们的状态 x 就是水位 level。
    # 注意：这里的KF实现没有B*u项，我们在循环中手动处理输入的影响
    F = np.array([[1.0]]) # 状态转移矩阵 (水位自己不会变，除非有输入)
    H = np.array([[1.0]]) # 观测矩阵 (我们直接观测水位)

    # 过程噪声Q: 代表我们对模型有多不信任 (面积不准、未知入渗等)
    Q = np.array([[0.01**2]]) # 假设模型每步有1cm的不确定性
    # 测量噪声R: 代表我们对传感器有多不信任
    R = np.array([[0.1**2]]) # 假设传感器有10cm的测量误差

    # 初始状态估计和不确定性
    x0 = np.array([5.0])
    P0 = np.array([[1.0]])

    kf = KalmanFilter(F=F, H=H, Q=Q, R=R, x0=x0, P0=P0)

    # 3. 仿真循环
    num_steps = 120 # 模拟120分钟
    results = { 'time': [], 'true_level': [], 'open_loop_level': [], 'kf_level': [], 'measurement': [] }

    inflow = 10.0 # 恒定入流

    print("Running Kalman Filter simulation...")
    for i in range(num_steps):
        # 更新“真实”模型
        true_model.input.inflow = inflow
        true_model.step(dt)

        # 更新“开环”模型 (无修正)
        open_loop_model.input.inflow = inflow
        open_loop_model.step(dt)

        # --- 卡尔曼滤波核心步骤 ---
        # 1. 预测
        kf.predict()

        # 2. 加入模型输入的影响 (在KF类外)
        # 我们的模型是 level_k = level_{k-1} + (inflow/area)*dt
        # kf.predict() 只是计算了 level_k = level_{k-1}
        # 我们需要手动加上输入项
        model_input_effect = (inflow / kf_model.area) * dt
        kf.x[0] += model_input_effect

        # 3. 生成带噪声的测量值
        measurement = true_model.level + np.random.normal(0, np.sqrt(R[0,0]))

        # 4. 更新
        kf.update(np.array([measurement]))

        # 获取修正后的状态，并用它更新我们的数字孪生模型
        corrected_level = kf.get_state()[0]
        kf_model.level = corrected_level

        # 记录数据
        results['time'].append(i * dt / 60)
        results['true_level'].append(true_model.level)
        results['open_loop_level'].append(open_loop_model.level)
        results['kf_level'].append(corrected_level)
        results['measurement'].append(measurement)
    print("Simulation finished.")

    # 4. 绘图
    plt.figure(figsize=(15, 8))
    plt.title('第十八章: 卡尔曼滤波数据同化效果', fontsize=16)
    plt.plot(results['time'], results['true_level'], 'b-', linewidth=3, label='真实水位')
    plt.plot(results['time'], results['open_loop_level'], 'r--', label='开环模型预测 (参数不准)')
    plt.plot(results['time'], results['measurement'], 'ko', markersize=2, alpha=0.4, label='带噪声的测量值')
    plt.plot(results['time'], results['kf_level'], 'g-', linewidth=2, label='卡尔曼滤波修正后的水位')
    plt.xlabel('时间 (分钟)')
    plt.ylabel('水位 (m)')
    plt.legend()
    plt.grid(True)
    plt.show()
    # output_dir = 'results/ch18'
    # os.makedirs(output_dir, exist_ok=True)
    # output_path = os.path.join(output_dir, 'ch18_kalman_filter.png')
    # plt.savefig(output_path)
    # plt.close()
    # print(f"Plot saved to {output_path}")

if __name__ == "__main__":
    run_kalman_filter_simulation()
