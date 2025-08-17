import matplotlib.pyplot as plt
import numpy as np

# This is a simple way to make the SDK accessible to the script.
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from chs_sdk.modules.modeling.pipeline_model import PipelineModel
from chs_sdk.modules.modeling.valve_models import ButterflyValve
from chs_sdk.modules.modeling.st_venant_model import StVenantModel
from chs_sdk.agents.control_agents import PIDAgent

def run_simulation():
    """
    This script simulates a hybrid pressurized-pipe and open-channel system,
    demonstrating how to manually couple the models in a simulation loop.
    """
    # 1. 初始化各个模型
    # Note: Using simplified models for this programmatic example.
    # A real-world case would use a more integrated solver or approach.
    pipe = PipelineModel(name='TunnelPipe', length=5000, diameter=3.0, friction_factor=0.018)
    valve = ButterflyValve(name='ControlValve', cv_max=50.0, travel_time=120.0)

    channel_nodes = [{'name': 'Inlet', 'type': 'inflow', 'bed_elevation': 10.0},
                     {'name': 'Outlet', 'type': 'level', 'initial_level': 12.0, 'bed_elevation': 8.0}]
    channel_reaches = [{'name': 'MainChannel', 'from_node': 'Inlet', 'to_node': 'Outlet',
                        'length': 10000, 'num_cells': 20, 'manning': 0.025,
                        'shape': 'trapezoidal', 'params': {'bottom_width': 10, 'side_slope': 2}}]
    channel = StVenantModel(nodes_data=channel_nodes, reaches_data=channel_reaches)

    pid = PIDAgent(name='FlowPID', setpoint=20.0, kp=0.1, ki=0.02, output_min=0.0, output_max=1.0)

    # 2. 仿真循环与手动耦合
    num_steps = 1800 # 模拟30分钟
    dt = 1.0 # 秒
    results = {'time':[], 'pipe_flow':[], 'channel_inflow':[], 'channel_inlet_level':[], 'valve_opening':[]}

    upstream_pressure = 100.0 # 恒定上游压力

    print("Running hybrid system simulation...")
    for i in range(num_steps):
        # --- 核心耦合逻辑 ---
        # 1. 获取明渠入口的水位，作为管道+阀门的下游压力
        channel_state = channel.get_state()
        downstream_pressure = channel_state['nodes']['Inlet']['head']

        # 2. 运行PID控制器
        #    PID的测量值是阀门的流量
        pid.set_input('measured_value', valve.flow)
        pid.step(dt=dt)

        # 3. 运行阀门模型
        valve.set_input('command', pid.get_port('output').value)
        # 阀门的直接上游是管道出口，为简化，我们假设阀门紧贴管道出口，
        # 其上游压力等于管道出口压力。而管道出口压力又取决于管道内的动态。
        # 这是一个复杂的相互作用，这里我们用一个简化方式：
        # 假设阀门感受到的是源头压力，这是一个很大的简化。
        valve.step(upstream_pressure, downstream_pressure, dt)

        # 4. 运行管道模型
        #    管道的下游压力应是阀门的入口压力。
        #    这里我们再次简化，假设管道直接连接到渠道入口。
        pipe.step(upstream_pressure, downstream_pressure, dt)

        # 5. 获取阀门的出流量，作为明渠的入流边界
        channel_inflow = valve.flow
        channel.set_boundary_condition('Inlet', 'inflow', channel_inflow)

        # 6. 运行明渠模型
        channel.step(dt)

        # 记录结果
        results['time'].append(i*dt/60) # in minutes
        results['pipe_flow'].append(pipe.flow)
        results['channel_inflow'].append(channel_inflow)
        results['channel_inlet_level'].append(downstream_pressure)
        results['valve_opening'].append(valve.get_current_opening())
    print("Simulation finished.")

    # 3. 绘图
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    fig.suptitle('第二十八章: 有压-无压混合系统仿真', fontsize=16)

    # 图1: 流量
    ax1.plot(results['time'], results['channel_inflow'], 'b-', label='渠道入口流量 (阀门控制后)')
    ax1.axhline(y=20.0, color='r', linestyle='--', label='目标流量')
    ax1.set_ylabel('流量 (m³/s)'); ax1.legend(); ax1.grid(True)

    # 图2: 状态变量
    ax2.plot(results['time'], results['valve_opening'], 'g-', label='阀门开度')
    ax2.set_ylabel('开度 (0-1)', color='g'); ax2.tick_params(axis='y', labelcolor='g');
    ax2.legend(loc='upper left')

    ax2b = ax2.twinx()
    ax2b.plot(results['time'], results['channel_inlet_level'], 'm--', label='渠道入口水位 (右轴)')
    ax2b.set_ylabel('水位 (m)', color='m'); ax2b.tick_params(axis='y', labelcolor='m');
    ax2b.legend(loc='upper right')

    ax2.set_xlabel('时间 (分钟)')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95]); plt.show()


if __name__ == "__main__":
    run_simulation()
