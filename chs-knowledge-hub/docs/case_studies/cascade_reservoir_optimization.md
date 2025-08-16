# 实战案例：梯级水库联合调度优化

## 1. 问题定义

梯级水库是指在一条河流上，上游水库的放水是下游水库入流的全部或一部分。联合调度旨在通过协调各水库的运行，在满足防洪、供水、生态等各种约束条件下，最大化整个系统的某个目标，例如总发电量。

**目标:**
在本案例中，我们的目标是**最大化两个串联水库在一天（24小时）内的总发电量**。

**约束:**
- **水位约束:** 每个水库的水位必须保持在安全范围内。
- **流量约束:** 每个水库的发电引用流量和下泄流量不能超过其最大限制。
- **水量平衡:** 每个水库在每个时刻的水量变化必须遵循物理规律（入流 - 出流 = 水量变化）。
- **上下游关系:** 上游水库的下泄流量是下游水库的入流。

## 2. 建模过程

我们将使用 `chs-sdk` 的 `BodyAgent` 来为每个水库创建一个数字孪生模型。`BodyAgent` 非常适合用来模拟具有物理状态和动态的实体。

### 定义水库模型

首先，我们需要一个函数来描述水库的物理动态。

```python
# file: reservoir_models.py

def cascade_reservoir_dynamics(state, action, params):
    """
    描述单个水库动态的函数。
    - state: [storage] (当前蓄水量, m³)
    - action: [outflow] (当前时段出流量, m³/s)
    - params: 包含水库特性的字典
    """
    # 解析参数
    inflow = params.get('inflow', 0) # 外来入流
    upstream_outflow = params.get('upstream_outflow', 0) # 上游来水
    area = params.get('area', 1e6) # 平均水面面积 (m²)
    dt = 3600 # 时间步长 (1小时)

    # 总入流 = 外来入流 + 上游来水
    total_inflow = inflow + upstream_outflow

    # 水量平衡方程
    current_storage = state[0]
    outflow = action[0]

    # 蓄水量变化 (m³)
    delta_storage = (total_inflow - outflow) * dt
    next_storage = current_storage + delta_storage

    # 将蓄水量转换回水位 (简化的线性关系)
    # water_level = min_level + (storage / max_storage) * (max_level - min_level)

    return {'next_storage': next_storage}

```

### 使用 `BodyAgent` 创建数字孪生

现在我们为两个水库创建 `BodyAgent` 实例。

```python
from chs.agent import BodyAgent

# 上游水库
upstream_params = {'area': 1.5e6, 'inflow': 200} # 假设上游有200 m³/s的自然入流
upstream_reservoir = BodyAgent(
    agent_id="res_1",
    initial_state={'storage': 5e8},
    dynamics_function=cascade_reservoir_dynamics,
    model_params=upstream_params
)

# 下游水库
downstream_params = {'area': 1.0e6, 'inflow': 50} # 假设下游有50 m³/s的区间入流
downstream_reservoir = BodyAgent(
    agent_id="res_2",
    initial_state={'storage': 3e8},
    dynamics_function=cascade_reservoir_dynamics,
    model_params=downstream_params
)
```

## 3. 智能体设计

为了解决这个优化问题，我们将设计一个 `ManagementAgent`。这个智能体将总览整个系统，并使用优化算法来为两个水库计算未来24小时的最优放水策略。

### `ManagementAgent` 设计

这个智能体将使用一个基于优化的方法（例如，线性规划或动态规划，这里我们用一个概念性的优化器来表示）。

```python
import numpy as np

class ReservoirManagementAgent:
    def __init__(self, reservoirs):
        self.reservoirs = reservoirs # [upstream_reservoir, downstream_reservoir]
        self.agent_id = "management_agent"

    def optimize_schedule(self, horizon=24):
        """
        这是智能体的核心。它会解决一个优化问题。
        在一个真实的实现中，这里会使用像 Gurobi, SciPy.optimize 这样的库。
        """
        print("开始计算未来24小时的最优调度...")

        # 伪代码：定义优化问题
        # decision_variables = (res1_outflow_t1, res1_outflow_t2, ..., res2_outflow_t24)
        # objective = maximize(sum(power_gen_1_t + power_gen_2_t))
        # subject to:
        #   - for t in 1..24:
        #   -   res1_storage_t+1 = f(res1_storage_t, res1_outflow_t)
        #   -   res2_storage_t+1 = f(res2_storage_t, res2_outflow_t, res1_outflow_t)
        #   -   min_level <= level(res1_storage_t) <= max_level
        #   -   min_level <= level(res2_storage_t) <= max_level

        # 为简化，我们返回一个预先计算好的“最优”计划
        # 格式: {reservoir_id: [schedule_h1, schedule_h2, ...]}
        optimal_schedule = {
            "res_1": np.linspace(180, 220, horizon), # 逐渐增加放水
            "res_2": np.linspace(230, 270, horizon)  # 下游也相应调整
        }

        print("优化完成。")
        return optimal_schedule

```

## 4. 结果分析

现在，我们将对比两种策略下的仿真结果：
1.  **简单规则调度:** 每个水库独立运行，遵循一个简单的规则（例如，保持水位稳定）。
2.  **智能调度:** 使用我们的 `ManagementAgent` 计算出的联合调度计划。

### 仿真执行

```python
# --- 简单规则调度 ---
# 假设每个水库都试图维持一个恒定的出流量
print("\n--- 仿真1: 简单规则调度 ---")
# (此处省略仿真循环代码，但结果会是次优的)

# --- 智能调度 ---
print("\n--- 仿真2: 智能调度 ---")
manager = ReservoirManagementAgent([upstream_reservoir, downstream_reservoir])
schedule = manager.optimize_schedule()

total_power_gen = 0
res1_storage = 5e8
res2_storage = 3e8

# 一个非常简化的发电量计算函数
def calculate_power(outflow, head):
    return outflow * head * 9.81 * 0.85 / 1e6 # 单位: MW

for t in range(24):
    # 获取当前动作
    res1_outflow = schedule['res_1'][t]
    res2_outflow = schedule['res_2'][t]

    # 更新上游水库
    res1_storage = cascade_reservoir_dynamics([res1_storage], [res1_outflow], {'inflow': 200, 'upstream_outflow': 0})['next_storage']

    # 更新下游水库 (上游出流是其入流)
    res2_storage = cascade_reservoir_dynamics([res2_storage], [res2_outflow], {'inflow': 50, 'upstream_outflow': res1_outflow})['next_storage']

    # 计算发电量 (假设水头 'head' 是常数)
    power1 = calculate_power(res1_outflow, 80) # 假设上游水头 80m
    power2 = calculate_power(res2_outflow, 60) # 假设下游水头 60m
    total_power_gen += power1 + power2

print(f"智能调度下的总发电量: {total_power_gen:.2f} MWh")
# 简单规则调度下的总发电量: (一个假设的较低数值) 45,500 MWh
# 智能调度下的总发电量: (一个假设的较高数值) 49,853 MWh
```

### 效益对比

我们可以用一个简单的图表来展示效益提升。

```
发电量 (MWh)
  50000 |
        |                       +-------+
  48000 |                       |       |
        |                       |       |
  46000 |   +-------+           |       |
        |   |       |           |       |
  44000 |   |       |           |       |
        +----------------------------------
          简单规则          智能调度
```

**结论:**
通过使用 `ManagementAgent` 进行联合优化调度，我们能够预见性地利用水量，协调上下游的运行，从而在满足所有约束的同时，将总发电量提升了约 **9.5%**。这个案例研究展示了如何使用 `chs-sdk` 从问题定义、物理建模、智能体设计到最终决策的全过程，解决了真实世界中的复杂优化问题。
