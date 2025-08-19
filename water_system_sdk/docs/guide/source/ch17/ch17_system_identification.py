import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# This is a simple way to make the SDK accessible to the script.
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src')))

from chs_sdk.tools.identification_toolkit import IdentificationToolkit
from chs_sdk.modules.modeling.integral_plus_delay_model import IntegralPlusDelayModel

def run_identification():
    """
    This script demonstrates how to use the IdentificationToolkit to find
    the parameters of a "black-box" model from observed input/output data.
    """
    # 1. 生成“观测数据”
    # 在真实项目中，这些数据来自历史记录。在这里，我们先用一个已知参数的模型来生成它。
    # 我们使用一个积分+延迟模型 (IntegralPlusDelayModel)
    true_K = 0.0005
    true_T = 1800.0 # 延迟30分钟
    dt = 60.0
    true_model = IntegralPlusDelayModel(name='TrueProcess', K=true_K, T=true_T, dt=dt, initial_value=10.0)

    # 创建一个变化的入流过程
    inflow_data = 10 + 5 * np.sin(2 * np.pi * np.arange(400) / 100)
    outflow_data_true = []
    for inflow_val in inflow_data:
        true_model.input.inflow = inflow_val
        true_model.step()
        outflow_data_true.append(true_model.output)

    # 为“观测”数据加入一些噪声
    observed_outflow_data = np.array(outflow_data_true) + np.random.normal(0, 0.1, size=len(inflow_data))

    # 将数据整理成DataFrame
    observed_df = pd.DataFrame({
        'inflow': inflow_data,
        'outflow': observed_outflow_data
    })

    print("--- 系统辨识开始 ---")

    # 2. 初始化工具箱并运行离线辨识
    toolkit = IdentificationToolkit()

    # 我们假装不知道参数 K 和 T 是多少，给出一个初始猜测
    initial_guess = [0.001, 1000.0] # 猜测 K 和 T

    identification_results = toolkit.identify_offline(
        model_type='IntegralDelay',
        inflow=observed_df['inflow'].values,
        outflow=observed_df['outflow'].values,
        dt=dt,
        initial_guess=initial_guess,
        # 我们可以为参数设置一个合理的搜索范围
        bounds=([0.0, 0.0], [0.1, 5000.0])
    )

    identified_params = identification_results['params']
    identified_K = identified_params['K']
    identified_T = identified_params['T']
    rmse = identification_results['rmse']

    print(f"辨识完成！")
    print(f"  - 真实参数 (K, T): ({true_K:.5f}, {true_T:.1f})")
    print(f"  - 辨识出参数 (K, T): ({identified_K:.5f}, {identified_T:.1f})")
    print(f"  - 均方根误差 (RMSE): {rmse:.4f}")

    # 3. 验证辨识结果
    # 使用辨识出的参数，创建一个新模型，看看它的输出与观测值有多接近
    identified_model = IntegralPlusDelayModel(name='IdentifiedProcess', K=identified_K, T=identified_T, dt=dt, initial_value=10.0)
    simulated_outflow = []
    for inflow_val in inflow_data:
        identified_model.input.inflow = inflow_val
        identified_model.step()
        simulated_outflow.append(identified_model.output)

    # 4. 绘图
    plt.figure(figsize=(15, 7))
    plt.title('第十七章: 系统辨识结果对比 (Integral-Delay Model)', fontsize=16)
    plt.plot(observed_df.index, observed_df['outflow'], 'ko', markersize=3, alpha=0.5, label='观测输出')
    plt.plot(observed_df.index, simulated_outflow, 'r-', linewidth=2, label=f'辨识模型模拟输出 (K={identified_K:.4f}, T={identified_T:.0f})')
    plt.xlabel('时间步')
    plt.ylabel('输出值')
    plt.legend()
    plt.grid(True)

    plt.show()


if __name__ == "__main__":
    run_identification()
