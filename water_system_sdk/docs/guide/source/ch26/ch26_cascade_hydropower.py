import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
import pandas as pd

from chs_sdk.core.host import AgentKernel as Host
from chs_sdk.modules.modeling.storage_models import LinearTank, MuskingumChannelModel
from chs_sdk.modules.modeling.control_structure_models import HydropowerStationModel
from water_system_sdk.docs.guide.source.project_utils import ModelAgent, EulerMethod

def run_simulation():
    """
    This script simulates a cascade of two hydropower stations to demonstrate
    the hydraulic linkage and time lag caused by the connecting river reach.
    """
    host = Host()

    # 1. 创建组件
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='Reservoir1',
        model_class=LinearTank,
        area=5e6,
        initial_level=100.0)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='HydroStation1',
        model_class=HydropowerStationModel,
        max_flow_area=50.0,
        discharge_coeff=0.9,
        efficiency=0.85)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='RiverReach',
        model_class=MuskingumChannelModel,
        K=6*3600.0,
        x=0.2,
        dt=1800.0,
        initial_inflow=10,
        initial_outflow=10)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='Reservoir2',
        model_class=LinearTank,
        area=4e6,
        initial_level=50.0)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='HydroStation2',
        model_class=HydropowerStationModel,
        max_flow_area=50.0,
        discharge_coeff=0.9,
        efficiency=0.85)

    # 2. 建立连接
    res1 = host._agents['Reservoir1']
    hs1 = host._agents['HydroStation1']
    reach = host._agents['RiverReach']
    res2 = host._agents['Reservoir2']
    hs2 = host._agents['HydroStation2']

    hs1.subscribe(f"{res1.agent_id}/level", 'upstream_level')
    res1.subscribe(f"{hs1.agent_id}/output", 'release_outflow')
    reach.subscribe(f"{hs1.agent_id}/output", 'inflow')
    res2.subscribe(f"{reach.agent_id}/output", 'inflow')
    hs2.subscribe(f"{res2.agent_id}/level", 'upstream_level')
    res2.subscribe(f"{hs2.agent_id}/output", 'release_outflow')

    # 3. 仿真循环与开环调度
    dt_seconds = 1800.0
    num_steps = int(48 * 3600 / dt_seconds)
    results = []
    host.start(time_step=dt_seconds)

    for i in range(num_steps):
        current_hour = (i * dt_seconds / 3600) % 24

        if 8 <= current_hour < 20:
            vane_opening = 0.9
        else:
            vane_opening = 0.2

        hs1.input_values['vane_opening'] = vane_opening
        hs1.input_values['downstream_level'] = 55.0
        hs2.input_values['vane_opening'] = vane_opening
        hs2.input_values['downstream_level'] = 15.0

        host.tick()

        results.append({
            'time': host.current_time,
            'Reservoir1.level': res1.model.level,
            'Reservoir2.level': res2.model.level,
            'HydroStation1.flow': hs1.model.flow,
            'RiverReach.outflow': reach.model.output
        })

    # 4. 绘图
    results_df = pd.DataFrame(results)
    time_hours = results_df['time'] / 3600

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    fig.suptitle('第二十六章: 梯级水电站联动仿真', fontsize=16)

    ax1.plot(time_hours, results_df['HydroStation1.flow'], 'b-', label='上游电站出流')
    ax1.plot(time_hours, results_df['RiverReach.outflow'], 'r--', label='下游水库入流 (滞后)')
    ax1.set_ylabel('流量 (m^3/s)'); ax1.legend(); ax1.grid(True)

    ax2.plot(time_hours, results_df['Reservoir1.level'], 'b-', label='上游水库水位')
    ax2b = ax2.twinx()
    ax2b.plot(time_hours, results_df['Reservoir2.level'], 'g--', label='下游水库水位 (右轴)')
    ax2.set_xlabel('时间 (小时)'); ax2.set_ylabel('上游水位 (m)'); ax2b.set_ylabel('下游水位 (m)')

    lines, labels = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2b.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='best')
    ax2.grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95]); plt.show()

if __name__ == "__main__":
    run_simulation()
