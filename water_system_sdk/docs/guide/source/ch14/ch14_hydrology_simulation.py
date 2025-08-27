import json
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
import pandas as pd
import os
import sys
import networkx as nx

# 添加水系统SDK源码路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../src')))

import numpy as np

def simple_xinanjiang_runoff(precipitation_mm, evaporation_mm, params, dt_hours):
    """简化的新安江模型"""
    K = params.get('K', 0.2)
    IM = params.get('IM', 0.05)
    C = params.get('C', 0.15)
    
    # 不透水面积产流
    impervious_runoff = precipitation_mm * IM
    
    # 透水面积产流（简化处理）
    pervious_runoff = max(0, (precipitation_mm - evaporation_mm) * C)
    
    total_runoff_mm = impervious_runoff + pervious_runoff
    return total_runoff_mm

def muskingum_routing(inflow, prev_inflow, prev_outflow, K, x, dt):
    """Muskingum河道演算模型"""
    if K <= 0:
        return inflow
    
    # 计算Muskingum系数
    denominator = K - K * x + 0.5 * dt
    if denominator == 0:
        return inflow
    
    C1 = (0.5 * dt - K * x) / denominator
    C2 = (0.5 * dt + K * x) / denominator
    C3 = (K - K * x - 0.5 * dt) / denominator
    
    outflow = C1 * inflow + C2 * prev_inflow + C3 * prev_outflow
    return max(0, outflow)

class SimpleBasin:
    """简化的流域仿真类"""
    def __init__(self, topology_data, params_data, timeseries_data):
        self.topology_data = topology_data
        self.params_data = params_data
        self.timeseries_data = timeseries_data
        
    def run_simulation(self):
        """运行水文仿真"""
        dt_hours = self.timeseries_data["time_step_hours"]
        num_steps = len(self.timeseries_data["data"]["SubBasin1"]["precipitation_mm"])
        
        # 初始化状态变量
        subbasin1_prev_inflow = 5.0
        subbasin1_prev_outflow = 5.0
        subbasin2_prev_inflow = 0.0
        subbasin2_prev_outflow = 0.0
        
        # 运行仿真
        results = {
            'SubBasin1': np.zeros(num_steps),
            'SubBasin2': np.zeros(num_steps),
            'outlet': np.zeros(num_steps)
        }
        
        for t in range(num_steps):
            # SubBasin1: 计算产流
            precip1 = self.timeseries_data["data"]["SubBasin1"]["precipitation_mm"][t]
            evap1 = self.timeseries_data["data"]["SubBasin1"]["evaporation_mm"][t]
            params1 = self.params_data["SubBasin1"]["runoff_parameters"]
            
            subbasin1_runoff_mm = simple_xinanjiang_runoff(precip1, evap1, params1, dt_hours)
            subbasin1_runoff_m3s = subbasin1_runoff_mm * 150 * 1000 / (dt_hours * 3600)  # 150 km²
            
            # SubBasin1: 河道演算到SubBasin2
            routing_params1 = self.params_data["SubBasin1"]["routing_parameters"]
            subbasin1_outflow = muskingum_routing(
                subbasin1_runoff_m3s, 
                subbasin1_prev_inflow, 
                subbasin1_prev_outflow,
                routing_params1["K"], 
                routing_params1["x"], 
                routing_params1["dt"]
            )
            
            # 更新SubBasin1状态
            subbasin1_prev_inflow = subbasin1_runoff_m3s
            subbasin1_prev_outflow = subbasin1_outflow
            
            # SubBasin2: 计算本地产流
            precip2 = self.timeseries_data["data"]["SubBasin2"]["precipitation_mm"][t]
            evap2 = self.timeseries_data["data"]["SubBasin2"]["evaporation_mm"][t]
            params2 = self.params_data["SubBasin2"]["runoff_parameters"]
            
            subbasin2_runoff_mm = simple_xinanjiang_runoff(precip2, evap2, params2, dt_hours)
            subbasin2_runoff_m3s = subbasin2_runoff_mm * 100 * 1000 / (dt_hours * 3600)  # 100 km²
            
            # SubBasin2: 总入流 = 本地产流 + 上游来水
            subbasin2_total_inflow = subbasin2_runoff_m3s + subbasin1_outflow
            
            # SubBasin2: 河道演算到出口
            routing_params2 = self.params_data["SubBasin2"]["routing_parameters"]
            outlet_flow = muskingum_routing(
                subbasin2_total_inflow,
                subbasin2_prev_inflow,
                subbasin2_prev_outflow,
                routing_params2["K"],
                routing_params2["x"],
                routing_params2["dt"]
            )
            
            # 更新SubBasin2状态
            subbasin2_prev_inflow = subbasin2_total_inflow
            subbasin2_prev_outflow = outlet_flow
            
            # 记录结果
            results['SubBasin1'][t] = subbasin1_outflow
            results['SubBasin2'][t] = subbasin2_total_inflow
            results['outlet'][t] = outlet_flow
        
        return results

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

    # 2. 创建 SimpleBasin 对象并运行仿真
    print("Initializing SimpleBasin model and running simulation...")
    basin = SimpleBasin(
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
    print("完整仿真结果:")
    for i in range(len(results_df)):
        print(f"时间 {i} 小时: SubBasin1={results_df.iloc[i]['SubBasin1']:.2f}, SubBasin2={results_df.iloc[i]['SubBasin2']:.2f}, Outlet={results_df.iloc[i]['outlet']:.2f}")
    print("\nDataFrame格式:")
    print(results_df)

    # 创建时间轴
    time_hours = np.arange(len(results_df)) * timeseries_data["time_step_hours"]
    
    # 绘图
    plt.figure(figsize=(16, 10))  # 调整图形尺寸适应2*2布局
    
    # 第一行：拓扑图 + 降雨时间序列
    # 拓扑图
    plt.subplot(2, 2, 1)
    
    # 创建有向图
    G = nx.DiGraph()
    
    # 添加节点 - 调整位置避免重叠
    G.add_node('SubBasin1', pos=(0.15, 0.8), area='150 km^2', type='sub_basin')
    G.add_node('SubBasin2', pos=(0.85, 0.6), area='100 km^2', type='sub_basin')
    G.add_node('Outlet', pos=(0.85, 0.2), area='', type='outlet')
    
    # 添加边
    G.add_edge('SubBasin1', 'SubBasin2', label='Reach1\n(Muskingum)')
    G.add_edge('SubBasin2', 'Outlet', label='Reach2\n(Muskingum)')
    
    # 获取节点位置
    pos = nx.get_node_attributes(G, 'pos')
    
    # 绘制节点 - 增大节点大小
    node_colors = ['lightblue', 'lightgreen', 'lightcoral']
    node_sizes = [3500, 3200, 2800]  # 增大节点大小
    
    nx.draw_networkx_nodes(G, pos, 
                          node_color=node_colors,
                          node_size=node_sizes,
                          alpha=0.8,
                          edgecolors='black',
                          linewidths=2)
    
    # 绘制边 - 调整箭头大小和位置，连接到圆圈边缘
    nx.draw_networkx_edges(G, pos, 
                          edge_color='darkblue',
                          arrows=True,
                          arrowsize=15,  # 减小箭头大小
                          arrowstyle='->',
                          width=2.5,     # 减小边宽度
                          alpha=0.7,
                          connectionstyle="arc3,rad=0.1",  # 添加弧度避免重叠
                          node_size=node_sizes)  # 传递节点大小，让边连接到边缘
    
    # 绘制节点标签
    nx.draw_networkx_labels(G, pos, 
                           labels={'SubBasin1': 'SubBasin1\n(150 km^2)',
                                  'SubBasin2': 'SubBasin2\n(100 km^2)',
                                  'Outlet': 'Outlet'},
                           font_size=9,
                           font_weight='bold')
    
    # 绘制边标签 - 调整位置避免重叠
    edge_labels = nx.get_edge_attributes(G, 'label')
    # 手动调整边标签位置
    edge_label_pos = {
        ('SubBasin1', 'SubBasin2'): (0.5, 0.7),
        ('SubBasin2', 'Outlet'): (0.85, 0.4)
    }
    
    for edge, label in edge_labels.items():
        plt.text(edge_label_pos[edge][0], edge_label_pos[edge][1], 
                label, ha='center', va='center', fontsize=8,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8))
    
    plt.title('流域拓扑结构', fontsize=12, fontweight='bold')
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.axis('off')
    
    # 添加整体黑框，起到视觉对齐效果
    rect = plt.Rectangle((0, 0), 1, 1, linewidth=3, edgecolor='black', facecolor='none')
    plt.gca().add_patch(rect)
    
    # 降雨数据 - 改为柱状图
    plt.subplot(2, 2, 2)
    x_pos = np.arange(len(time_hours))
    width = 0.35
    
    plt.bar(x_pos - width/2, timeseries_data["data"]["SubBasin1"]["precipitation_mm"], 
            width, label='SubBasin1降雨 (mm)', color='lightblue', alpha=0.8)
    plt.bar(x_pos + width/2, timeseries_data["data"]["SubBasin2"]["precipitation_mm"], 
            width, label='SubBasin2降雨 (mm)', color='lightgreen', alpha=0.8)
    
    plt.title('降雨时间序列')
    plt.xlabel('时间 (h)')
    plt.ylabel('降雨量 (mm)')
    plt.xticks(x_pos, [f'{int(t)}' for t in time_hours])
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 第二行：流量仿真结果 + 产流过程分析
    # 流量结果
    plt.subplot(2, 2, 3)
    plt.plot(time_hours, results_df['SubBasin1'], 'b-o', label='SubBasin1出流 (m^3/s)')
    plt.plot(time_hours, results_df['SubBasin2'], 'g-s', label='SubBasin2总入流 (m^3/s)')
    plt.plot(time_hours, results_df['outlet'], 'r-^', label='流域出口流量 (m^3/s)')
    plt.title('流量仿真结果')
    plt.xlabel('时间 (h)')
    plt.ylabel('流量 (m^3/s)')
    plt.legend()
    plt.grid(True)
    
    # 产流过程分析 - 改为柱状图
    plt.subplot(2, 2, 4)
    # 计算每个子流域的产流深度
    subbasin1_runoff_depth = []
    subbasin2_runoff_depth = []
    dt_hours = timeseries_data["time_step_hours"]  # 获取时间步长
    for t in range(len(time_hours)):
        precip1 = timeseries_data["data"]["SubBasin1"]["precipitation_mm"][t]
        evap1 = timeseries_data["data"]["SubBasin1"]["evaporation_mm"][t]
        params1 = params_data["SubBasin1"]["runoff_parameters"]
        runoff1 = simple_xinanjiang_runoff(precip1, evap1, params1, dt_hours)
        subbasin1_runoff_depth.append(runoff1)
        
        precip2 = timeseries_data["data"]["SubBasin2"]["precipitation_mm"][t]
        evap2 = timeseries_data["data"]["SubBasin2"]["evaporation_mm"][t]
        params2 = params_data["SubBasin2"]["runoff_parameters"]
        runoff2 = simple_xinanjiang_runoff(precip2, evap2, params2, dt_hours)
        subbasin2_runoff_depth.append(runoff2)
    
    # 使用柱状图展示产流深度
    x_pos = np.arange(len(time_hours))
    width = 0.35
    
    plt.bar(x_pos - width/2, subbasin1_runoff_depth, 
            width, label='SubBasin1产流深度 (mm)', color='lightblue', alpha=0.8)
    plt.bar(x_pos + width/2, subbasin2_runoff_depth, 
            width, label='SubBasin2产流深度 (mm)', color='lightgreen', alpha=0.8)
    
    plt.title('产流过程分析')
    plt.xlabel('时间 (h)')
    plt.ylabel('产流深度 (mm)')
    plt.xticks(x_pos, [f'{int(t)}' for t in time_hours])
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    # output_dir = 'results/ch14'
    # os.makedirs(output_dir, exist_ok=True)
    # output_path = os.path.join(output_dir, 'ch14_hydrology_simulation.png')
    # plt.savefig(output_path)
    # plt.close()
    # print(f"Plot saved to {output_path}")

if __name__ == "__main__":
    run_simulation()
