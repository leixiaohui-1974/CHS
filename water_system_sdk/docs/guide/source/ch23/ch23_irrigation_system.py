import matplotlib.pyplot as plt
import pandas as pd

from chs_sdk.core.host import AgentKernel as Host
from chs_sdk.modules.modeling.storage_models import LinearTank, MuskingumChannelModel
from chs_sdk.modules.modeling.control_structure_models import SluiceGate
from water_system_sdk.docs.guide.source.project_utils import ModelAgent, EulerMethod

def run_simulation():
    """
    This script simulates a simple irrigation network, demonstrating how
    to connect multiple components in a branching topology.
    """
    host = Host()

    # 1. 创建组件
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='Reservoir',
        model_class=LinearTank,
        area=1e6,
        initial_level=20.0)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='HeadGate',
        model_class=SluiceGate,
        gate_width=5.0,
        discharge_coeff=0.8)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='MainCanal',
        model_class=MuskingumChannelModel,
        K=2*3600.0,
        x=0.2,
        dt=60.0,
        initial_inflow=0,
        initial_outflow=0)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='BranchCanal1',
        model_class=MuskingumChannelModel,
        K=1*3600.0,
        x=0.2,
        dt=60.0,
        initial_inflow=0,
        initial_outflow=0)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='BranchCanal2',
        model_class=MuskingumChannelModel,
        K=1.5*3600.0,
        x=0.2,
        dt=60.0,
        initial_inflow=0,
        initial_outflow=0)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='BranchGate1',
        model_class=SluiceGate,
        gate_width=1.5,
        discharge_coeff=0.8)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='BranchGate2',
        model_class=SluiceGate,
        gate_width=1.5,
        discharge_coeff=0.8)

    # 2. 建立连接
    reservoir = host._agents['Reservoir']
    head_gate = host._agents['HeadGate']
    main_canal = host._agents['MainCanal']
    branch_canal1 = host._agents['BranchCanal1']
    branch_canal2 = host._agents['BranchCanal2']
    branch_gate1 = host._agents['BranchGate1']
    branch_gate2 = host._agents['BranchGate2']

    head_gate.subscribe(f"{reservoir.agent_id}/level", 'upstream_level')
    main_canal.subscribe(f"{head_gate.agent_id}/output", 'inflow')
    branch_canal1.subscribe(f"{branch_gate1.agent_id}/output", 'inflow')
    branch_canal2.subscribe(f"{branch_gate2.agent_id}/output", 'inflow')

    # 3. 运行仿真与开环控制
    num_steps = int(6 * 3600 / 60)
    dt = 60.0
    results = []
    host.start(time_step=dt)

    # 初始时，所有闸门关闭
    head_gate.input_values['command'] = 0.0
    branch_gate1.input_values['command'] = 0.0
    branch_gate2.input_values['command'] = 0.0
    head_gate.input_values['downstream_level'] = 18.0

    for i in range(num_steps):
        if i == 10:
            print("Time 10 min: Opening head gate.")
            head_gate.input_values['command'] = 0.8
        if i == 3 * 60:
            print("Time 3 hr: Opening branch gate 1.")
            branch_gate1.input_values['command'] = 0.5
        if i == 4 * 60:
            print("Time 4 hr: Opening branch gate 2.")
            branch_gate2.input_values['command'] = 0.4

        main_canal_outflow = main_canal.model.output
        main_canal_water_level = 18.0 - 2.0 * (main_canal_outflow / 50.0)
        branch_gate1.input_values['upstream_level'] = main_canal_water_level
        branch_gate2.input_values['upstream_level'] = main_canal_water_level
        branch_gate1.input_values['downstream_level'] = 5.0
        branch_gate2.input_values['downstream_level'] = 5.0

        host.tick()
        results.append({
            'time': host.current_time,
            'MainCanal.outflow': main_canal.model.output,
            'BranchCanal1.outflow': branch_canal1.model.output,
            'BranchCanal2.outflow': branch_canal2.model.output,
        })

    # 4. 绘图
    results_df = pd.DataFrame(results)
    plt.figure(figsize=(15, 8))
    plt.title('第二十三章: 灌区系统水力调配仿真', fontsize=16)
    plt.plot(results_df['time'] / 60, results_df['MainCanal.outflow'], label='干渠出口流量')
    plt.plot(results_df['time'] / 60, results_df['BranchCanal1.outflow'], label='支渠1 出口流量')
    plt.plot(results_df['time'] / 60, results_df['BranchCanal2.outflow'], label='支渠2 出口流量')
    plt.xlabel('时间 (分钟)'); plt.ylabel('流量 (m³/s)'); plt.legend(); plt.grid(True)
    plt.show()

if __name__ == "__main__":
    run_simulation()
