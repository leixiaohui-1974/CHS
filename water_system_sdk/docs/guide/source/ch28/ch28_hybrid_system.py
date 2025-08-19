import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

from chs_sdk.modules.modeling.pipeline_model import PipelineModel
from chs_sdk.modules.modeling.valve_models import ButterflyValve
from chs_sdk.modules.modeling.st_venant_model import StVenantModel
from chs_sdk.modules.control.pid_controller import PIDController

def run_simulation():
    """
    This script simulates a hybrid pressurized-pipe and open-channel system,
    demonstrating how to manually couple the models in a simulation loop.
    """
    # 1. 初始化各个模型
    pipe = PipelineModel(name='TunnelPipe', length=5000, diameter=3.0, friction_factor=0.018)
    valve = ButterflyValve(name='ControlValve', cv_max=50.0, slew_rate=1.0/120.0)

    channel_nodes = [{'name': 'Inlet', 'type': 'inflow', 'bed_elevation': 10.0, 'inflow': 0.0},
                     {'name': 'Outlet', 'type': 'level', 'level': 12.0, 'bed_elevation': 8.0}]
    channel_reaches = [{'name': 'MainChannel', 'from_node': 'Inlet', 'to_node': 'Outlet',
                        'length': 10000, 'manning_coefficient': 0.025,
                        'bottom_width': 10, 'side_slope': 2}]
    channel = StVenantModel(nodes_data=channel_nodes, reaches_data=channel_reaches)

    pid = PIDController(name='FlowPID', set_point=20.0, Kp=0.1, Ki=0.02, Kd=0.0, output_min=0.0, output_max=1.0)

    # 2. 仿真循环与手动耦合
    num_steps = 1800
    dt = 1.0
    results = {'time':[], 'pipe_flow':[], 'channel_inflow':[], 'channel_inlet_level':[], 'valve_opening':[]}

    upstream_pressure = 100.0

    print("Running hybrid system simulation...")
    for i in range(num_steps):
        channel_state = channel.get_state()
        downstream_pressure = channel_state['nodes']['Inlet']['head']

        pid.step(dt=dt, error_source=valve.output)

        valve.step(upstream_pressure, downstream_pressure, dt, command=pid.output)

        pipe.step(upstream_pressure, downstream_pressure, dt)

        channel_inflow = valve.output
        channel.network.get_node('Inlet').inflow = channel_inflow

        channel.step(dt)

        results['time'].append(i*dt/60)
        results['pipe_flow'].append(pipe.output)
        results['channel_inflow'].append(channel_inflow)
        results['channel_inlet_level'].append(downstream_pressure)
        results['valve_opening'].append(valve.get_current_opening())
    print("Simulation finished.")

    # 3. 绘图
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    fig.suptitle('第二十八章: 有压-无压混合系统仿真', fontsize=16)

    ax1.plot(results['time'], results['channel_inflow'], 'b-', label='渠道入口流量 (阀门控制后)')
    ax1.axhline(y=20.0, color='r', linestyle='--', label='目标流量')
    ax1.set_ylabel('流量 (m^3/s)'); ax1.legend(); ax1.grid(True)

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
