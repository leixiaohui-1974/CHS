import matplotlib.pyplot as plt

# This is a simple way to make the SDK accessible to the script.
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from chs_sdk.core.host import Host
from chs_sdk.modules.modeling.storage_models import LinearTank
from chs_sdk.modules.modeling.valve_models import GenericValve
from chs_sdk.agents.control_agents import PIDAgent
from chs_sdk.agents.dispatch_agent import DispatchAgent
from chs_sdk.agents.message import MacroCommandMessage

def run_simulation():
    """
    This script demonstrates a hierarchical control system where a high-level
    DispatchAgent sends a new command to a low-level PIDAgent mid-simulation.
    """
    host = Host()

    # 1. 创建物理层组件
    tank1 = LinearTank(name='Tank1', area=1000.0, initial_level=10.0)
    # A simplified valve where flow is proportional to opening
    valve1 = GenericValve(name='Valve1', cv_curve=[0, 10.0], travel_time=10.0)
    tank2 = LinearTank(name='Tank2', area=800.0, initial_level=10.0)
    valve2 = GenericValve(name='Valve2', cv_curve=[0, 8.0], travel_time=10.0)

    # 2. 创建战术层 (PID控制器)
    pid1 = PIDAgent(name='PID1', setpoint=10.0, kp=0.8, ki=0.1)
    pid2 = PIDAgent(name='PID2', setpoint=10.0, kp=0.9, ki=0.12)

    # 3. 创建战略层 (调度大脑)
    # 这个调度大脑将在第500秒时，向PID2发送一个新指令
    dispatch_logic = {
        500: MacroCommandMessage(
            topic="cmd/pid2/setpoint",
            sender_id="CentralDispatch",
            payload={"value": 12.0} # 新的目标水位
        )
    }
    dispatcher = DispatchAgent(name='CentralDispatch', dispatch_logic=dispatch_logic)

    # 4. 添加所有组件到主机
    host.add_agents([tank1, valve1, tank2, valve2, pid1, pid2, dispatcher])

    # 5. 连接
    # Tank1 的控制回路
    host.add_connection('Tank1', 'level', 'PID1', 'measured_value')
    host.add_connection('PID1', 'output', 'Valve1', 'command')
    # For this simple valve, we manually set pressures and connect flow.
    # In a real pipe network, pressures would come from other components.
    valve1.set_input('upstream_pressure', tank1.get_port('level'))
    valve1.set_input('downstream_pressure', 1.0) # Assume constant downstream pressure
    host.add_connection('Valve1', 'flow', 'Tank1', 'release_outflow')

    # Tank2 的控制回路
    host.add_connection('Tank2', 'level', 'PID2', 'measured_value')
    host.add_connection('PID2', 'output', 'Valve2', 'command')
    valve2.set_input('upstream_pressure', tank2.get_port('level'))
    valve2.set_input('downstream_pressure', 1.0)
    host.add_connection('Valve2', 'flow', 'Tank2', 'release_outflow')

    # 6. 运行仿真
    print("Running hierarchical dispatch simulation...")
    host.run(num_steps=1000, dt=1.0)
    print("Simulation finished.")

    # 7. 绘图
    results_df = host.get_datalogger().get_as_dataframe()
    plt.figure(figsize=(15, 7))
    plt.title('第二十一章: 分层优化调度仿真', fontsize=16)
    plt.plot(results_df.index, results_df['Tank1.level'], label='水库1 水位')
    plt.plot(results_df.index, results_df['Tank2.level'], label='水库2 水位', linewidth=2)
    plt.axhline(y=12.0, color='r', linestyle='--', label='水库2 新目标水位')
    plt.xlabel('时间 (秒)'); plt.ylabel('水位 (m)'); plt.legend(); plt.grid(True)
    plt.show()

if __name__ == "__main__":
    run_simulation()
