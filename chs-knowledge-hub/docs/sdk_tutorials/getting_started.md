# 10分钟构建你的第一个虚拟水库

## 简介

欢迎来到CHS-SDK的世界！本教程将引导你在10分钟内，利用CHS-SDK构建一个功能完备的虚拟水库仿真模型。你将学会如何定义水库、设计控制规则、运行仿真，并最终将结果可视化。

让我们开始吧！

## 步骤 1: 搭建“舞台” (环境)

首先，我们需要导入仿真所需的“道具”——水库（`Reservoir`）和闸门站（`SluiceStation`）。这就像在拍摄电影前，先要搭好场景。

```python
import pandas as pd
import matplotlib.pyplot as plt
from chs_sdk.agents.body import Reservoir
from chs_sdk.agents.control import SluiceStation

# 实例化水库
# initial_storage: 初始有效蓄水量 (万m³)
# capacity: 有效库容 (万m³)
# dead_storage: 死库容 (万m³)
reservoir = Reservoir(
    name="测试水库",
    initial_storage=3000,
    capacity=10000,
    dead_storage=500
)

# 实例化闸门站
# max_outflow: 最大下泄流量 (m³/s)
sluice_station = SluiceStation(
    name="测试闸门站",
    max_outflow=1000
)

print("水库和闸门站创建成功！")
print(f"水库当前水位: {reservoir.get_water_level()} m")
```

这段代码创建了一个具有特定初始水量和库容的`Reservoir`实例，以及一个具有最大流量限制的`SluiceStation`实例。

## 步骤 2: 设计“演员” (智能体)

现在，我们需要一位“演员”来根据规则操作闸门。我们来创建一个简单的基于规则的智能体`SimpleRuleAgent`。

```python
from chs_sdk.agents.base import BaseAgent

class SimpleRuleAgent(BaseAgent):
    """一个简单的基于规则的决策智能体"""
    def decide(self, observation):
        """
        决策函数
        :param observation: 来自环境的观测数据
        :return: 动作
        """
        water_level = observation['water_level']

        # 规则：如果水位超过80米，则全开闸门；否则，关闭闸门。
        if water_level > 80:
            action = {'outflow_rate': 1.0} # 1.0 代表最大下泄流量的100%
        else:
            action = {'outflow_rate': 0.0} # 0.0 代表关闭

        return action

# 实例化智能体
agent = SimpleRuleAgent(name="规则智能体")
print("智能体创建成功！")
```

这个`SimpleRuleAgent`的逻辑非常简单：当它“感知”到水位超过80米时，就做出“决策”，将闸门全开。

## 步骤 3: “导演”就位，开拍！ (仿真主循环)

万事俱备！现在让“导演”——仿真主循环——登场，推动整个故事的发展。这个循环将模拟“感知->决策->执行->演化”的完整过程。

```python
from chs_sdk.core.host import CHSHost

# 创建一个仿真Host
host = CHSHost()

# 注册我们的水库和闸门站
host.add_body(reservoir)
host.add_control(sluice_station)

# 模拟的入库流量数据 (m³/s)
inflow_data = [100, 120, 150, 800, 1200, 1100, 900, 700, 500, 300]
results = []

# 开始仿真
for step, inflow in enumerate(inflow_data):
    # 1. 感知 (Perceive)
    observation = host.perceive()

    # 2. 决策 (Decide)
    action = agent.decide(observation)

    # 3. 执行 (Execute)
    host.execute(action)

    # 4. 演化 (Evolve)
    host.evolve(inflow=inflow)

    # 记录当前状态
    current_state = {
        "step": step,
        "inflow": inflow,
        "water_level": reservoir.get_water_level(),
        "storage": reservoir.storage,
        "outflow": sluice_station.current_outflow
    }
    results.append(current_state)
    print(f"Step {step}: 水位={current_state['water_level']:.2f}m, 出库流量={current_state['outflow']:.2f}m³/s")

# 将结果转换为DataFrame
results_df = pd.DataFrame(results)
print("\n仿真完成！")
```

在这个循环中，`CHSHost`负责协调所有组件，模拟了随时间变化的入库流量下，智能体如何根据水库状态做出反应。

## 步骤 4: 查看“样片” (数据可视化)

最后，我们来看看仿真的“样片”——也就是结果。使用`pandas`和`matplotlib`可以轻松地将数据可视化。

```python
# 创建图表
fig, ax1 = plt.subplots(figsize=(12, 6))

# 绘制水位变化
ax1.plot(results_df['step'], results_df['water_level'], 'b-', label='Water Level (m)')
ax1.set_xlabel('Time Step')
ax1.set_ylabel('Water Level (m)', color='b')
ax1.tick_params('y', colors='b')

# 创建第二个y轴，绘制流量变化
ax2 = ax1.twinx()
ax2.plot(results_df['step'], results_df['inflow'], 'g--', label='Inflow (m³/s)')
ax2.plot(results_df['step'], results_df['outflow'], 'r:', label='Outflow (m³/s)')
ax2.set_ylabel('Flow Rate (m³/s)', color='g')
ax2.tick_params('y', colors='g')

# 添加图例和标题
fig.tight_layout()
fig.legend(loc='upper left', bbox_to_anchor=(0.1, 0.9))
plt.title('Virtual Reservoir Simulation Results')
plt.grid(True)
plt.show()

print(results_df)
```

这段代码会生成一张清晰的图表，展示了在整个仿真过程中，水位、入库流量和出库流量的变化情况。

恭喜！你已经成功构建并运行了你的第一个虚拟水库模型。这只是一个开始，CHS-SDK拥有更强大的功能等待你去探索。
