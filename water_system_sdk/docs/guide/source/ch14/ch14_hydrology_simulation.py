import json
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
import pandas as pd
import os

from chs_sdk.modules.hydrology.core import Basin

def run_simulation():
    """
    This script runs a configuration-driven hydrological simulation for a
    simple two-sub-basin watershed.
    """
    # Define the relative path to the data files
    source_dir = os.path.dirname(__file__)

    # 1. 加载配置文件
    try:
        with open(os.path.join(source_dir, 'ch14_topology.json'), 'r') as f:
            topology_data = json.load(f)
        with open(os.path.join(source_dir, 'ch14_parameters.json'), 'r') as f:
            params_data = json.load(f)
        with open(os.path.join(source_dir, 'ch14_timeseries.json'), 'r') as f:
            timeseries_data = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: Could not find a required data file. Make sure all JSON files are in the same directory as this script.")
        print(e)
        return

    # 2. 创建 Basin 对象并运行仿真
    print("Initializing Basin model and running simulation...")
    basin = Basin(
        topology_data=topology_data,
        params_data=params_data,
        timeseries_data=timeseries_data
    )
    results = basin.run_simulation()
    print("Simulation finished.")

    # 3. 绘图
    results_df = pd.DataFrame(results)
    results_df.index.name = "Time (hours)"
    print("\n仿真结果:")
    print(results_df)

    results_df.plot(figsize=(12, 7), grid=True, style=['-o', '-s'])
    plt.title('第十四章: 流域水文仿真结果')
    plt.xlabel('时间 (小时)')
    plt.ylabel('流量 (m^3/s)')
    plt.legend(title='出口位置')
    plt.show()
    # output_dir = 'results/ch14'
    # os.makedirs(output_dir, exist_ok=True)
    # output_path = os.path.join(output_dir, 'ch14_hydrology_simulation.png')
    # plt.savefig(output_path)
    # plt.close()
    # print(f"Plot saved to {output_path}")

if __name__ == "__main__":
    run_simulation()
