import numpy as np
import matplotlib.pyplot as plt

# This is a simple way to make the SDK accessible to the script.
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from chs_sdk.core.host import Host
from chs_sdk.modules.modeling.storage_models import LinearTank
from chs_sdk.modules.modeling.control_structure_models import GateModel, PumpStationModel
from chs_sdk.modules.control.rule_based_controller import RuleBasedOperationalController
from chs_sdk.modules.disturbances.predefined import TimeSeriesDisturbance

def run_simulation():
    """
    This script demonstrates how to use a RuleBasedOperationalController
    to implement operational dispatch logic for a reservoir.
    """
    host = Host()

    # 1. 创建组件
    reservoir = LinearTank(name='MainReservoir', area=2000.0, initial_level=5.0)
    inlet_gate = GateModel(name='InletGate', gate_width=2.0, discharge_coeff=0.8)
    outlet_pump = PumpStationModel(name='OutletPump', num_pumps_total=1, curve_coeffs=[-0.001, 0.05, 20])

    # 创建一个变化的上游来水过程
    inflow_disturbance = TimeSeriesDisturbance(
        name='UpstreamInflow',
        times=[0, 200, 201, 1000],
        values=[5, 5, 20, 20] # 模拟一次洪水过程
    )

    # 2. 定义规则控制器
    rules = [
        {
            "if": [{"variable": "MainReservoir.level", "operator": ">", "value": 15.0}],
            "then": {"gate_opening": 0.0, "pump_command": 1} # 防洪：关闸、开泵
        },
        {
            "if": [{"variable": "MainReservoir.level", "operator": "<", "value": 3.0}],
            "then": {"gate_opening": 1.0, "pump_command": 0} # 兴利：开闸、关泵
        }
    ]
    default_actions = {"gate_opening": 0.5, "pump_command": 0} # 正常：半开闸、关泵

    dispatcher = RuleBasedOperationalController(
        name='ReservoirDispatcher',
        rules=rules,
        default_actions=default_actions
    )

    # 3. 添加到主机并连接
    host.add_agent(reservoir)
    host.add_agent(inlet_gate)
    host.add_agent(outlet_pump)
    host.add_agent(inflow_disturbance)
    host.add_agent(dispatcher)

    # 控制器连接
    host.add_connection('ReservoirDispatcher', 'gate_opening', 'InletGate', 'command')
    host.add_connection('ReservoirDispatcher', 'pump_command', 'OutletPump', 'num_pumps_on')

    # 物理连接
    inlet_gate.set_input('upstream_level', 20.0) # 假设上游水源水位恒定
    inlet_gate.set_input('downstream_level', reservoir.get_port('level'))
    host.add_connection('InletGate', 'value', reservoir, 'inflow')

    outlet_pump.set_input('inlet_level', reservoir.get_port('level'))
    outlet_pump.set_input('outlet_level', 2.0) # 假设下游尾水位恒定
    host.add_connection('OutletPump', 'value', reservoir, 'release_outflow')

    host.add_connection('UpstreamInflow', 'value', reservoir, 'inflow') # 外部入流

    # 4. 运行仿真
    print("Running rule-based dispatch simulation...")
    host.run(num_steps=1000, dt=1.0)
    print("Simulation finished.")

    # 5. 绘图
    results_df = host.get_datalogger().get_as_dataframe()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    fig.suptitle('第二十章: 基于规则的水库调度仿真', fontsize=16)

    ax1.plot(results_df.index, results_df['MainReservoir.level'], 'b-', label='水库水位')
    ax1.axhline(y=15.0, color='r', linestyle='--', label='汛限水位 (15m)')
    ax1.axhline(y=3.0, color='g', linestyle='--', label='兴利水位 (3m)')
    ax1.set_ylabel('水位 (m)')
    ax1.legend(); ax1.grid(True)

    ax2.plot(results_df.index, results_df['ReservoirDispatcher.gate_opening'], 'c-', label='闸门开度指令')
    ax2.plot(results_df.index, results_df['ReservoirDispatcher.pump_command'], 'm--', label='水泵开关指令')
    ax2.set_xlabel('时间 (秒)'); ax2.set_ylabel('调度指令'); ax2.legend(); ax2.grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95]); plt.show()

if __name__ == "__main__":
    run_simulation()
