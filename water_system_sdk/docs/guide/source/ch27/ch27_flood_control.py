import json
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
import pandas as pd
import numpy as np
import os

from chs_sdk.modules.hydrology.core import Basin
from chs_sdk.core.host import AgentKernel as Host
from chs_sdk.modules.modeling.storage_models import NonlinearTank
from chs_sdk.modules.modeling.control_structure_models import SluiceGateWithOutput
from chs_sdk.modules.modeling.storage_models import MuskingumChannelModel
from chs_sdk.modules.control.rule_based_controller import RuleBasedOperationalController
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from project_utils import ModelAgent, EulerMethod

class SmartDispatchController:
    """智能调度控制器 - 实现基于预报信息的主动调度"""
    def __init__(self, forecast_peak):
        self.forecast_peak = forecast_peak
        
    def get_gate_opening(self, current_level, current_time_hour):
        """根据水位和预报信息计算闸门开度"""
        # 优化的预防性调度策略 - 更早开始主动调度
        if current_level >= 31.0:
            return 0.9  # 接近警戒水位，立即大幅泄洪
        elif current_level >= 30.0 and self.forecast_peak > 10000:
            return 0.8  # 预报大洪水且水位30m，大幅开启
        elif current_level >= 28.0 and self.forecast_peak > 5000:
            return 0.6  # 预报中等洪水且水位28m，中度开启
        elif current_level >= 26.0 and self.forecast_peak > 2000:
            return 0.4  # 预报有洪水且水位26m，开始泄洪
        elif current_level >= 24.0 and self.forecast_peak > 500:
            return 0.2  # 预报小洪水且水位24m，预防性泄洪
        else:
            return 0.0

class ForecastDataAgent:
    """预报数据智能体 - 专门提供预报信息给规则控制器"""
    def __init__(self, forecast_peak):
        self.forecast_peak = forecast_peak
    
    def get_state(self):
        return {"peak": self.forecast_peak}
    
    def step(self, dt):
        pass

def run_forecast_model():
    """Runs the hydrological forecast to get the inflow hydrograph."""
    print("--- Running Stage 1: Hydrological Forecast ---")
    source_dir = os.path.dirname(__file__)
    with open(os.path.join(source_dir, 'ch27_hydrology_topology.json'), 'r') as f:
        topology_data = json.load(f)
    with open(os.path.join(source_dir, 'ch27_hydrology_parameters.json'), 'r') as f:
        params_data = json.load(f)
    with open(os.path.join(source_dir, 'ch27_hydrology_timeseries.json'), 'r') as f:
        timeseries_data = json.load(f)

    basin = Basin(topology_data, params_data, timeseries_data)
    results = basin.run_simulation()
    forecasted_inflow = results['ReservoirInflow']
    print(f"预报完成 - 洪峰流量: {np.max(forecasted_inflow):.1f} m³/s")
    return forecasted_inflow

def run_dispatch_simulation(forecasted_inflow):
    """Runs the dispatch simulation using the forecast."""
    print("\n--- Running Stage 2: Flood Control Dispatch Simulation ---")
    host = Host()

    # 1. Create components - 恢复原始的库容曲线设计
    # 使用原始合理的库容参数，通过缩短时步提高计算精度
    level_volume_curve = np.array([[20.0, 22.0, 24.0, 26.0, 28.0, 30.0, 32.0, 35.0], 
                                   [0, 10e6, 25e6, 45e6, 70e6, 100e6, 140e6, 200e6]])
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='FloodControlReservoir',
        model_class=NonlinearTank,
        level_to_volume=level_volume_curve,
        initial_level=22.0)
    
    # 进一步增大闸门规格，确保充足的泄洪能力
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='SpillwayGate',
        model_class=SluiceGateWithOutput,
        gate_width=80.0,  # 进一步增大闸门宽度至80m
        discharge_coeff=0.95)  # 提高泄流系数至0.95
    
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='DownstreamReach',
        model_class=MuskingumChannelModel,
        K=2*3600,  # 缩短汇流时间
        x=0.3,
        dt=3600.0,
        initial_inflow=0,
        initial_outflow=0)

    forecast_peak = np.max(forecasted_inflow)
    
    # 添加预报数据智能体
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='ForecastData',
        model_class=ForecastDataAgent,
        forecast_peak=forecast_peak)
    
    # 极致的预防性调度规则 - 确保不超警戒水位的激进策略
    # 更早开始预防性泽洪，避免水位跳跃
    rules = [
        # 级别6：超过警戒水位立即全开
        {"if": [{"variable": "FloodControlReservoir.state.level", "operator": ">", "value": 32.0}], 
         "then": {"gate_opening": 1.0}},
        # 级别5：30.5m时大幅开启
        {"if": [{"variable": "FloodControlReservoir.state.level", "operator": ">", "value": 30.5}], 
         "then": {"gate_opening": 0.9}},
        # 级别4：预报超大洪水且水位达29m时大幅开启
        {"if": [{"variable": "ForecastData.state.peak", "operator": ">", "value": 2500}, 
                {"variable": "FloodControlReservoir.state.level", "operator": ">", "value": 29.0}], 
         "then": {"gate_opening": 0.8}},
        # 级别3：预报大洪水且水位达27m时中度开启
        {"if": [{"variable": "ForecastData.state.peak", "operator": ">", "value": 1500}, 
                {"variable": "FloodControlReservoir.state.level", "operator": ">", "value": 27.0}], 
         "then": {"gate_opening": 0.6}},
        # 级别2：预报中等洪水且水位达25m时开始泄洪
        {"if": [{"variable": "ForecastData.state.peak", "operator": ">", "value": 800}, 
                {"variable": "FloodControlReservoir.state.level", "operator": ">", "value": 25.0}], 
         "then": {"gate_opening": 0.4}},
        # 级别1：预报有洪水且水位达23m时预防性泄洪
        {"if": [{"variable": "ForecastData.state.peak", "operator": ">", "value": 300}, 
                {"variable": "FloodControlReservoir.state.level", "operator": ">", "value": 23.0}], 
         "then": {"gate_opening": 0.2}},
    ]
    default_actions = {"gate_opening": 0.0}
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='Dispatcher',
        model_class=RuleBasedOperationalController,
        rules=rules,
        default_actions=default_actions)

    # 2. Add agents and connect
    reservoir = host._agents['FloodControlReservoir']
    gate = host._agents['SpillwayGate']
    reach = host._agents['DownstreamReach']
    dispatcher = host._agents['Dispatcher']
    forecast_data = host._agents['ForecastData']

    gate.subscribe(f"{dispatcher.agent_id}/gate_opening", 'command')
    gate.subscribe(f"{reservoir.agent_id}/level", 'upstream_level')
    gate.input_values['downstream_level'] = 10.0

    reservoir.subscribe(f"{gate.agent_id}/output", 'release_outflow')
    # 修复：下游河道应该订阅闸门的output主题
    reach.subscribe(f"{gate.agent_id}/output", 'inflow')

    # 3. Run simulation with detailed logging
    num_steps = len(forecasted_inflow)
    dt = 1800.0  # 0.5小时 = 1800秒，提高计算精度
    results = []
    host.start(time_step=dt)

    print("\n调度过程详情:")
    print("时间  入流     水位   闸门开度  下泄流量  下游流量")
    print("(0.5h) (m³/s)   (m)     (%)     (m³/s)   (m³/s)")
    print("-" * 55)

    # 扩展预报数据以适应0.5小时时步（每小时数据重复2次）
    extended_inflow = []
    for i in range(len(forecasted_inflow)):
        extended_inflow.append(forecasted_inflow[i])  # 第一个0.5小时
        extended_inflow.append(forecasted_inflow[i])  # 第二个0.5小时
    
    total_steps = len(extended_inflow)
    
    for i in range(total_steps):
        # 设置入流 - 修复：同时设置 input_values 和 model.input
        reservoir.input_values['inflow'] = extended_inflow[i]
        reservoir.model.input.inflow = extended_inflow[i]  # 直接设置模型输入

        # 更新预报数据智能体
        forecast_data.on_execute(host.current_time, host.time_step)
        host.message_bus.dispatch()
        
        # 调度决策（不再需要extra_state，因为预报数据现在通过ForecastData智能体提供）
        dispatcher.on_execute(host.current_time, host.time_step)
        host.message_bus.dispatch()

        # 水库计算
        reservoir.on_execute(host.current_time, host.time_step)
        host.message_bus.dispatch()

        # 闸门计算
        gate.on_execute(host.current_time, host.time_step)
        host.message_bus.dispatch()
        
        # 修复：设置水库的出流信息，确保下一个时步的水量平衡正确
        spillway_flow = gate.model.output if hasattr(gate.model, 'output') else 0
        reservoir.model.input.release_outflow = spillway_flow

        # 下游河道计算
        reach.on_execute(host.current_time, host.time_step)
        host.message_bus.dispatch()

        host.current_time += dt

        # 收集详细数据
        gate_opening = dispatcher.model.get_state()['gate_opening']
        spillway_flow = gate.model.output if hasattr(gate.model, 'output') else 0
        downstream_flow = reach.model.output if hasattr(reach.model, 'output') else 0
        
        result_data = {
            'time': (i + 1) * 0.5,  # 0.5小时为单位
            'inflow': extended_inflow[i],
            'SpillwayGate.flow': spillway_flow,
            'FloodControlReservoir.level': reservoir.model.level,
            'gate_opening': gate_opening,
            'downstream_flow': downstream_flow
        }
        results.append(result_data)
        
        # 打印关键时段的信息（每小时打印一次或有显著流量时）
        if i < 20 or extended_inflow[i] > 100 or gate_opening > 0 or i % 2 == 1:  # 每小时打印
            print(f"{(i+1)*0.5:4.1f}   {extended_inflow[i]:8.1f}  {reservoir.model.level:6.2f}   "
                  f"{gate_opening*100:6.1f}   {spillway_flow:8.1f}  {downstream_flow:8.1f}")

    return pd.DataFrame(results)

def main():
    # Stage 1: Get the forecast
    forecasted_inflow = run_forecast_model()

    # Stage 2: Run the dispatch simulation
    dispatch_results_df = run_dispatch_simulation(forecasted_inflow)

    # --- Analysis ---
    print("\n--- 防洪调度效果分析 ---")
    max_level = dispatch_results_df['FloodControlReservoir.level'].max()
    natural_peak = np.max(forecasted_inflow)
    controlled_peak = dispatch_results_df['SpillwayGate.flow'].max()
    downstream_peak = dispatch_results_df['downstream_flow'].max()
    
    print(f"水库最高水位: {max_level:.2f}m")
    print(f"警戒水位: 32.0m")
    if max_level > 32.0:
        print(f"⚠️  超警戒 {max_level - 32.0:.2f}m")
    else:
        print(f"✅ 水位安全")
    
    print(f"\n洪峰削减效果:")
    print(f"天然洪峰: {natural_peak:.1f} m³/s")
    print(f"水库下泄洪峰: {controlled_peak:.1f} m³/s")
    print(f"下游实际洪峰: {downstream_peak:.1f} m³/s")
    if natural_peak > 0:
        reduction_rate = (natural_peak - downstream_peak) / natural_peak * 100
        print(f"总削减率: {reduction_rate:.1f}%")

    # --- Enhanced Plotting ---
    print("\n--- Plotting Results ---")
    time_hours = np.array([r['time'] for r in dispatch_results_df.to_dict('records')])  # 0.5小时为单位
    original_time_hours = np.arange(len(forecasted_inflow))  # 原始预报数据的时间轴

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('第二十七章: 预报-调度联动防洪仿真完整分析', fontsize=16)

    # 流量对比图
    # 扩展预报数据以匹配0.5小时时步
    extended_forecast = []
    for flow in forecasted_inflow:
        extended_forecast.extend([flow, flow])  # 每小时数据重复2次
    
    ax1.plot(time_hours, extended_forecast, 'b-', linewidth=2, label='天然入库流量')
    ax1.plot(time_hours, dispatch_results_df['SpillwayGate.flow'], 'r--', linewidth=2, label='水库下泄流量')
    ax1.plot(time_hours, dispatch_results_df['downstream_flow'], 'g:', linewidth=2, label='下游河道流量')
    ax1.set_ylabel('流量 (m³/s)')
    ax1.set_title('流量过程对比')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 水位变化图
    ax2.plot(time_hours, dispatch_results_df['FloodControlReservoir.level'], 'b-', linewidth=2, label='水库水位')
    ax2.axhline(y=32.0, color='red', linestyle='--', linewidth=2, label='警戒水位')
    ax2.axhline(y=35.0, color='orange', linestyle='--', alpha=0.7, label='设计水位')
    ax2.set_ylabel('水位 (m)')
    ax2.set_title('水库水位变化')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # 闸门开度图
    ax3.plot(time_hours, dispatch_results_df['gate_opening']*100, 'purple', linewidth=2, marker='o', markersize=4)
    ax3.set_ylabel('闸门开度 (%)')
    ax3.set_xlabel('时间 (小时)')
    ax3.set_title('闸门调度策略')
    ax3.set_ylim(-5, 105)
    ax3.grid(True, alpha=0.3)

    # 防洪效果对比图
    ax4.fill_between(time_hours, 0, extended_forecast, alpha=0.3, color='blue', label='天然洪水')
    ax4.fill_between(time_hours, 0, dispatch_results_df['downstream_flow'], alpha=0.7, color='green', label='调度后下游流量')
    ax4.set_ylabel('流量 (m³/s)')
    ax4.set_xlabel('时间 (小时)')
    ax4.set_title('防洪效果对比')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()
    
    # --- 防洪调度效果总结 ---
    print(f"\n" + "="*62)
    print(f"🏆               防洪调度效果总结")
    print(f"="*62)
    
    # 安全性评估
    if max_level <= 32.0:
        safety_status = "✅ 水库安全"
    elif max_level <= 35.0:
        safety_status = "⚠️  基本安全（超警戒但未超设计水位）"
    else:
        safety_status = "🚨 存在风险（超设计水位）"
    
    print(f"{safety_status}")
    print(f"✅ 洪峰削减: {reduction_rate:.1f}%")
    
    # 调度策略评估
    gate_operations = dispatch_results_df[dispatch_results_df['gate_opening'] > 0]
    if len(gate_operations) > 0:
        first_operation = gate_operations.iloc[0]
        print(f"✅ 预防性调度: 第{first_operation['time']:.0f}小时开始主动调度")
        print(f"✅ 调度水位: {first_operation['FloodControlReservoir.level']:.2f}m")
    
    # 总体效果评估
    if max_level <= 35.0 and reduction_rate > 80:
        print(f"🎉 防洪调度效果优秀！成功实现了预防性调度目标。")
    elif reduction_rate > 50:
        print(f"👍 防洪调度效果良好，基本达到了防洪目标。")
    else:
        print(f"⚠️  防洪调度效果一般，需要进一步优化调度策略。")
    
    print(f"="*62)

if __name__ == "__main__":
    main()
