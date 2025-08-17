import matplotlib.pyplot as plt

# This is a simple way to make the SDK accessible to the script.
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from chs_sdk.core.host import Host
from chs_sdk.modules.modeling.base_model import BaseModel
from chs_sdk.modules.modeling.storage_models import LinearTank

# 1. 创建自定义的蒸发模型
class EvaporationModel(BaseModel):
    """
    一个计算水体蒸发损失流量的自定义模型。
    """
    def __init__(self, name: str, evaporation_rate_mm_day: float):
        super().__init__(name=name)
        # 将蒸发速率从 mm/day 转换为 m/s
        self.rate_m_s = evaporation_rate_mm_day / 1000 / (24 * 3600)
        self.surface_area_m2 = 0.0
        self.evaporation_flow = 0.0
        self.output = self.evaporation_flow

    def step(self, surface_area: float, dt: float):
        """
        计算蒸发流量。
        输入:
            surface_area (float): 当前的水面面积 (m²)。
            dt (float): 时间步长 (s)，虽然在本模型中未使用，但保留它是好习惯。
        """
        self.surface_area_m2 = surface_area
        self.evaporation_flow = self.surface_area_m2 * self.rate_m_s
        self.output = self.evaporation_flow # 更新标准输出端口
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
    reservoir = LinearTank(name='MyReservoir', area=5e5, initial_level=20.0)
    # 创建我们的自定义模型实例
    evaporation = EvaporationModel(name='Evaporation', evaporation_rate_mm_day=5.0)

    # 3. 添加到主机并连接
    host.add_agents([reservoir, evaporation])
    # 将蒸发模型的流量，作为水库的一个出流
    host.add_connection('Evaporation', 'value', 'MyReservoir', 'release_outflow')

    # 4. 运行仿真
    # 我们需要在每个时间步手动为蒸发模型提供水面面积输入
    num_steps = 365 * 24 # 模拟一年
    dt = 3600.0 # 1小时

    print("Running simulation with custom model...")
    for i in range(num_steps):
        # 手动设置输入
        # 在这个例子中，水面面积是恒定的
        evaporation.set_input('surface_area', reservoir.area)
        host.step(dt)
    print("Simulation finished.")

    # 5. 绘图
    results_df = host.get_datalogger().get_as_dataframe()
    time_days = results_df.index * dt / (24 * 3600)

    plt.figure(figsize=(12, 7))
    plt.title('第三十章: 自定义蒸发模型对水库水位的影响', fontsize=16)
    plt.plot(time_days, results_df['MyReservoir.level'], label='水库水位')
    plt.xlabel('时间 (天)')
    plt.ylabel('水位 (m)')
    plt.legend(); plt.grid(True)
    plt.show()


if __name__ == "__main__":
    run_simulation_with_custom_model()
