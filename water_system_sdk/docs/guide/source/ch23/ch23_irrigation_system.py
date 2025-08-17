import matplotlib.pyplot as plt

# This is a simple way to make the SDK accessible to the script.
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from chs_sdk.core.host import Host
from chs_sdk.modules.modeling.storage_models import LinearTank, MuskingumChannelModel
from chs_sdk.modules.modeling.control_structure_models import GateModel

def run_simulation():
    """
    This script simulates a simple irrigation network, demonstrating how
    to connect multiple components in a branching topology.
    """
    host = Host()

    # 1. 创建组件
    # 水源
    reservoir = LinearTank(name='Reservoir', area=1e6, initial_level=20.0)
    # 渠首闸
    head_gate = GateModel(name='HeadGate', gate_width=5.0, discharge_coeff=0.8)

    # 三条渠道
    # NOTE: Using a simplified connection for the demo. A real model would need
    # a proper junction node to enforce mass balance.
    main_canal = MuskingumChannelModel(name='MainCanal', K=2*3600.0, x=0.2, dt=60.0, initial_inflow=0, initial_outflow=0)
    branch_canal1 = MuskingumChannelModel(name='BranchCanal1', K=1*3600.0, x=0.2, dt=60.0, initial_inflow=0, initial_outflow=0)
    branch_canal2 = MuskingumChannelModel(name='BranchCanal2', K=1.5*3600.0, x=0.2, dt=60.0, initial_inflow=0, initial_outflow=0)

    # 两个分水闸
    branch_gate1 = GateModel(name='BranchGate1', gate_width=1.5, discharge_coeff=0.8)
    branch_gate2 = GateModel(name='BranchGate2', gate_width=1.5, discharge_coeff=0.8)

    # 2. 添加到主机
    host.add_agents([reservoir, head_gate, main_canal, branch_canal1, branch_canal2, branch_gate1, branch_gate2])

    # 3. 连接
    # 水库 -> 渠首闸 -> 干渠
    head_gate.set_input('upstream_level', reservoir.get_port('level'))
    # A more realistic model would have the downstream level be the actual channel water level
    head_gate.set_input('downstream_level', 18.0)
    host.add_connection('HeadGate', 'flow', 'MainCanal', 'inflow')

    # 干渠末端 -> 两个分水闸
    # This is a simplification. A mass-balance junction node would be needed here.
    # We assume the gates draw from the outflow of the main canal.
    # And the upstream level for the gates is based on the main canal's state.
    # This part of the model is conceptually flawed but works for a simple demo.
    main_canal_outflow = main_canal.get_port('outflow')
    # A better model would have a 'water_level_at_outlet' port.
    main_canal_water_level = 18.0 - 2.0 * (main_canal_outflow.value / 50.0) # Fake water level

    branch_gate1.set_input('upstream_level', main_canal_water_level)
    branch_gate2.set_input('upstream_level', main_canal_water_level)
    branch_gate1.set_input('downstream_level', 5.0)
    branch_gate2.set_input('downstream_level', 5.0)

    # 分水闸 -> 支渠
    host.add_connection('BranchGate1', 'flow', 'BranchCanal1', 'inflow')
    host.add_connection('BranchGate2', 'flow', 'BranchCanal2', 'inflow')

    # 4. 运行仿真与开环控制
    num_steps = int(6 * 3600 / 60) # 模拟6小时，每分钟一步
    print(f"Running irrigation system simulation for {num_steps} steps...")

    # 初始时，所有闸门关闭
    head_gate.set_input('command', 0.0)
    branch_gate1.set_input('command', 0.0)
    branch_gate2.set_input('command', 0.0)

    for i in range(num_steps):
        # 在第10分钟，开启渠首闸
        if i == 10:
            print("Time 10 min: Opening head gate.")
            head_gate.set_input('command', 0.8) # 开80%
        # 在第3小时，开启支渠1的闸门
        if i == 3 * 60:
            print("Time 3 hr: Opening branch gate 1.")
            branch_gate1.set_input('command', 0.5) # 开50%
        # 在第4小时，开启支渠2的闸门
        if i == 4 * 60:
            print("Time 4 hr: Opening branch gate 2.")
            branch_gate2.set_input('command', 0.4) # 开40%

        host.step(dt=60.0)
    print("Simulation finished.")

    # 5. 绘图
    results_df = host.get_datalogger().get_as_dataframe()
    plt.figure(figsize=(15, 8))
    plt.title('第二十三章: 灌区系统水力调配仿真', fontsize=16)
    plt.plot(results_df.index / 60, results_df['MainCanal.outflow'], label='干渠出口流量')
    plt.plot(results_df.index / 60, results_df['BranchCanal1.outflow'], label='支渠1 出口流量')
    plt.plot(results_df.index / 60, results_df['BranchCanal2.outflow'], label='支渠2 出口流量')
    plt.xlabel('时间 (分钟)'); plt.ylabel('流量 (m³/s)'); plt.legend(); plt.grid(True)
    plt.show()

if __name__ == "__main__":
    run_simulation()
