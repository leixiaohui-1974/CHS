import matplotlib.pyplot as plt
from chs_sdk.core.host import Host
from chs_sdk.modules.modeling.storage_models import FirstOrderStorageModel
from chs_sdk.modules.disturbances.predefined import TimeSeriesDisturbance

def run_simulation():
    """
    This script simulates the peak shaving effect of a stormwater detention pond
    on a runoff hydrograph.
    """
    host = Host()

    # 1. 定义入流洪水波
    # 模拟一场2小时的暴雨径流，洪峰在1小时处
    inflow_times = [0, 1*3600, 2*3600]  # 秒
    inflow_values = [0, 5.0, 0]        # m³/s
    inflow_hydrograph = TimeSeriesDisturbance(
        name='RunoffInflow',
        times=inflow_times,
        values=inflow_values
    )

    # 2. 创建调蓄池模型
    # time_constant 较大，表示出口较小，泄流缓慢
    detention_pond = FirstOrderStorageModel(
        name='DetentionPond',
        initial_value=0.0,
        time_constant=3*3600 # 泄流时间常数为3小时
    )

    # 3. 添加到主机并连接
    host.add_agent(inflow_hydrograph)
    host.add_agent(detention_pond)
    host.add_connection('RunoffInflow', 'value', 'DetentionPond', 'inflow')

    # 4. 运行仿真
    host.run(num_steps=6*3600, dt=60.0) # 模拟6小时，每分钟一步

    # 5. 绘图
    results_df = host.get_datalogger().get_as_dataframe()
    print("仿真结果 (前5行):")
    print(results_df.head())

    plt.figure(figsize=(12, 7))
    plt.title('第十三章: 雨水调蓄池削峰作用仿真', fontsize=16)

    plt.plot(results_df.index / 3600, results_df['RunoffInflow.value'], 'b-', label='入池流量 (径流)')
    plt.plot(results_df.index / 3600, results_df['DetentionPond.outflow'], 'r--', label='出池流量 (削峰后)')

    plt.xlabel('时间 (小时)')
    plt.ylabel('流量 (m³/s)')
    plt.legend()
    plt.grid(True)

    # 标注洪峰流量
    inflow_peak = results_df['RunoffInflow.value'].max()
    outflow_peak = results_df['DetentionPond.outflow'].max()
    plt.text(1.1, inflow_peak, f'入流洪峰: {inflow_peak:.2f} m³/s')
    plt.text(2.5, outflow_peak, f'出流洪峰: {outflow_peak:.2f} m³/s')

    plt.show()

if __name__ == "__main__":
    run_simulation()
