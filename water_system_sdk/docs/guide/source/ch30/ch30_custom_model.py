import matplotlib.pyplot as plt
import pandas as pd

from chs_sdk.core.host import AgentKernel as Host
from chs_sdk.modules.modeling.base_model import BaseModel
from chs_sdk.modules.modeling.storage_models import LinearTank
from water_system_sdk.docs.guide.source.project_utils import ModelAgent

# 1. 创建自定义的蒸发模型
class EvaporationModel(BaseModel):
    """
    一个计算水体蒸发损失流量的自定义模型。
    """
    def __init__(self, evaporation_rate_mm_day: float, **kwargs):
        super().__init__(**kwargs)
        self.rate_m_s = evaporation_rate_mm_day / 1000 / (24 * 3600)
        self.surface_area_m2 = 0.0
        self.evaporation_flow = 0.0
        self.output = self.evaporation_flow

    def step(self, surface_area: float, dt: float, **kwargs):
        self.surface_area_m2 = surface_area
        self.evaporation_flow = self.surface_area_m2 * self.rate_m_s
        self.output = self.evaporation_flow
        return self.output

    def get_state(self):
        return {
            "evaporation_rate_ms": self.rate_m_s,
            "surface_area_m2": self.surface_area_m2,
            "flow": self.evaporation_flow
        }

def run_simulation_with_custom_model():
    """
    This script demonstrates how to create a custom model by inheriting
    from BaseModel and how to integrate it into a simulation.
    """
    host = Host()

    # 2. 创建组件实例
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='MyReservoir',
        model_class=LinearTank,
        area=5e5,
        initial_level=20.0)
    host.add_agent(
        agent_class=ModelAgent,
        agent_id='Evaporation',
        model_class=EvaporationModel,
        evaporation_rate_mm_day=5.0)

    # 3. 建立连接
    reservoir_agent = host._agents['MyReservoir']
    evaporation_agent = host._agents['Evaporation']
    reservoir_agent.subscribe(f"{evaporation_agent.agent_id}/output", 'release_outflow')

    # 4. 运行仿真
    num_steps = 365 * 24
    dt = 3600.0
    results = []
    host.start(time_step=dt)

    for i in range(num_steps):
        evaporation_agent.input_values['surface_area'] = reservoir_agent.model.area
        host.tick()
        results.append({
            'time': host.current_time,
            'MyReservoir.level': reservoir_agent.model.level
        })

    # 5. 绘图
    results_df = pd.DataFrame(results)
    time_days = results_df['time'] / (24 * 3600)

    plt.figure(figsize=(12, 7))
    plt.title('第三十章: 自定义蒸发模型对水库水位的影响', fontsize=16)
    plt.plot(time_days, results_df['MyReservoir.level'], label='水库水位')
    plt.xlabel('时间 (天)')
    plt.ylabel('水位 (m)')
    plt.legend(); plt.grid(True)
    plt.show()


if __name__ == "__main__":
    run_simulation_with_custom_model()
