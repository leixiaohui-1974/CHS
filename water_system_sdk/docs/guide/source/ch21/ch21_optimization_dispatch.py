import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
import pandas as pd

from chs_sdk.core.host import AgentKernel as Host
from chs_sdk.modules.modeling.storage_models import LinearTank
from chs_sdk.modules.modeling.valve_models import GenericValve
from chs_sdk.agents.control_agents import PIDAgent
from chs_sdk.agents.message import Message
from water_system_sdk.docs.guide.source.project_utils import ModelAgent, SimpleDispatchAgent

def run_simulation():
    """
    This script demonstrates a hierarchical control system where a high-level
    DispatchAgent sends a new command to a low-level PIDAgent mid-simulation.
    """
    host = Host()

    # 1. 创建物理层组件
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='Tank1',
        model_class=LinearTank,
        area=1000.0,
        initial_level=10.0)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='Valve1',
        model_class=GenericValve,
        cv_curve=[0, 10.0],
        slew_rate=1.0/10.0)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='Tank2',
        model_class=LinearTank,
        area=800.0,
        initial_level=10.0)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='Valve2',
        model_class=GenericValve,
        cv_curve=[0, 8.0],
        slew_rate=1.0/10.0)

    # 2. 创建战术层 (PID控制器)
    host.add_agent(
        agent_class=PIDAgent,
        agent_id='PID1',
        Kp=0.8, Ki=0.1, Kd=0.0,
        set_point=10.0,
        input_topic="Tank1/level",
        output_topic="cmd/valve1/command")
    host.add_agent(
        agent_class=PIDAgent,
        agent_id='PID2',
        Kp=0.9, Ki=0.12, Kd=0.0,
        set_point=10.0,
        input_topic="Tank2/level",
        output_topic="cmd/valve2/command")

    # 3. 创建战略层 (调度大脑)
    dispatch_logic = {
        500: Message(
            topic="cmd/pid2/set_point",
            sender_id="CentralDispatch",
            payload={"value": 12.0}
        )
    }
    host.add_agent(
        agent_class=SimpleDispatchAgent,
        agent_id='CentralDispatch',
        dispatch_logic=dispatch_logic)

    # 4. 建立连接
    tank1 = host._agents['Tank1']
    valve1 = host._agents['Valve1']
    tank2 = host._agents['Tank2']
    valve2 = host._agents['Valve2']
    pid1 = host._agents['PID1']
    pid2 = host._agents['PID2']

    # Tank1 control loop
    valve1.subscribe("cmd/valve1/command", 'command')
    tank1.subscribe("Valve1/flow", 'release_outflow')

    # Tank2 control loop
    valve2.subscribe("cmd/valve2/command", 'command')
    tank2.subscribe("Valve2/flow", 'release_outflow')

    # Set boundary conditions
    valve1.input_values['upstream_pressure'] = 10.0
    valve1.input_values['downstream_pressure'] = 1.0
    valve2.input_values['upstream_pressure'] = 10.0
    valve2.input_values['downstream_pressure'] = 1.0


    # 5. 运行仿真
    num_steps = 1000
    dt = 1.0
    results = []
    host.start(time_step=dt)
    for i in range(num_steps):
        host.tick()
        results.append({
            'time': host.current_time,
            'Tank1.level': tank1.model.level,
            'Tank2.level': tank2.model.level,
        })

    # 6. 绘图
    results_df = pd.DataFrame(results)
    plt.figure(figsize=(15, 7))
    plt.title('第二十一章: 分层优化调度仿真', fontsize=16)
    plt.plot(results_df['time'], results_df['Tank1.level'], label='水库1 水位')
    plt.plot(results_df['time'], results_df['Tank2.level'], label='水库2 水位', linewidth=2)
    plt.axhline(y=12.0, color='r', linestyle='--', label='水库2 新目标水位')
    plt.xlabel('时间 (秒)'); plt.ylabel('水位 (m)'); plt.legend(); plt.grid(True)
    plt.show()

if __name__ == "__main__":
    run_simulation()
