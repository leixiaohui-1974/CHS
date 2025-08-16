# 高级教程：使用MPC实现预测控制

## 介绍

模型预测控制 (MPC) 是一种先进的过程控制方法，用于在满足一组约束条件的同时控制一个过程。CHS SDK 中的 `MPControlAgent` 使得在您的仿真中实施 MPC 变得简单。本教程将指导您完成设置和使用 `MPControlAgent` 的过程。

## 理论背景

MPC通过在有限的时间范围内优化控制输入来工作。在每个时间步，它会解决一个优化问题，以找到一系列能最小化成本函数（例如，与设定点的偏差）的未来控制动作。然后，它仅应用该序列的第一个控制动作，并在下一个时间步重复该过程。

这种方法使其能够预测未来的事件并相应地采取控制措施，从而实现更优的性能。

## 使用 `MPControlAgent`

`MPControlAgent` 需要一个系统模型、一个成本函数和约束。让我们为一个简单的水库建模，我们的目标是将其水位维持在一个期望的设定点。

### 1. 定义系统模型

首先，我们需要一个描述水库动态的函数。该函数将当前状态和控制输入作为参数，并返回下一个状态。

```python
import numpy as np

def reservoir_model(state, action, params):
    """
    一个简单的水库模型。
    状态: [水位]
    动作: [流入/流出速率]
    """
    dt = params.get('dt', 1.0) # 时间步长
    area = params.get('area', 100.0) # 水库表面积

    current_level = state[0]
    inflow_rate = action[0]

    # 水位变化 = (流入速率 * 时间步长) / 面积
    level_change = (inflow_rate * dt) / area
    next_level = current_level + level_change

    return np.array([next_level])
```

### 2. 配置 `MPControlAgent`

现在，我们将配置 `MPControlAgent`。我们需要定义状态、动作、约束和优化参数。

```python
from chs.agent import MPControlAgent

# MPC 参数
mpc_params = {
    'prediction_horizon': 10, # 预测范围
    'control_horizon': 3,     # 控制范围
    'state_dim': 1,
    'action_dim': 1,
    'model_function': reservoir_model,
    'model_params': {'dt': 1, 'area': 100},

    # 状态和动作的约束
    'state_bounds': np.array([[90, 110]]), # 水位必须在 90 和 110 之间
    'action_bounds': np.array([[-10, 10]]), # 流入/流出速率在 -10 和 10 之间

    # 成本函数权重
    'Q': np.diag([10.0]), # 状态偏差的权重
    'R': np.diag([1.0]),  # 控制动作的权重
}

# 创建智能体
mpc_agent = MPControlAgent(agent_id="reservoir_mpc_agent", **mpc_params)

# 设置目标（设定点）
setpoint = np.array([100.0]) # 目标水位
mpc_agent.set_target(setpoint)
```

### 3. 在仿真循环中运行

现在，我们可以在一个简单的仿真循环中使用这个智能体。

```python
# 初始状态
current_state = np.array([95.0]) # 初始水位

print(f"初始水位: {current_state[0]}")

# 仿真 20 个时间步
for t in range(20):
    # 计算下一个控制动作
    action = mpc_agent.compute_action(current_state)

    # 将动作应用到我们的（模拟）系统
    current_state = reservoir_model(current_state, action, mpc_params['model_params'])

    print(f"时间步 {t+1}: 动作 = {action[0]:.2f}, 新水位 = {current_state[0]:.2f}")

```

### 完整代码示例

```python
import numpy as np

# 假设的 CHS SDK 智能体类
class MPControlAgent:
    def __init__(self, agent_id, **kwargs):
        self.agent_id = agent_id
        self.params = kwargs
        self.target = None
        # 在一个真实的实现中，这里会初始化优化器
        print(f"MPControlAgent '{self.agent_id}' 已创建。")

    def set_target(self, target):
        self.target = target
        print(f"目标设定为: {self.target}")

    def compute_action(self, current_state):
        # 这是一个简化的模拟。在一个真实的场景中，
        # 这里会运行一个复杂的优化算法。
        if self.target is None:
            return np.zeros(self.params['action_dim'])

        error = self.target - current_state
        # 一个非常简单的比例控制器来模拟MPC的输出
        action = error * 0.5

        # 应用动作约束
        action_bounds = self.params['action_bounds']
        action = np.clip(action, action_bounds[:, 0], action_bounds[:, 1])

        return action

def reservoir_model(state, action, params):
    dt = params.get('dt', 1.0)
    area = params.get('area', 100.0)
    current_level = state[0]
    inflow_rate = action[0]
    level_change = (inflow_rate * dt) / area
    next_level = current_level + level_change
    return np.array([next_level])

# --- 仿真 ---

# MPC 参数
mpc_params = {
    'prediction_horizon': 10,
    'control_horizon': 3,
    'state_dim': 1,
    'action_dim': 1,
    'model_function': reservoir_model,
    'model_params': {'dt': 1, 'area': 100},
    'state_bounds': np.array([[90, 110]]),
    'action_bounds': np.array([[-10, 10]]),
    'Q': np.diag([10.0]),
    'R': np.diag([1.0]),
}

# 创建智能体
mpc_agent = MPControlAgent(agent_id="reservoir_mpc_agent", **mpc_params)

# 设置目标
setpoint = np.array([100.0])
mpc_agent.set_target(setpoint)

# 初始状态
current_state = np.array([95.0])
print(f"初始水位: {current_state[0]}")

# 仿真循环
for t in range(20):
    action = mpc_agent.compute_action(current_state)
    next_state = reservoir_model(current_state, action, mpc_params['model_params'])

    # 检查状态约束
    state_bounds = mpc_params['state_bounds']
    next_state = np.clip(next_state, state_bounds[:, 0], state_bounds[:, 1])

    current_state = next_state
    print(f"时间步 {t+1}: 动作 = {action[0]:.2f}, 新水位 = {current_state[0]:.2f}")
```

这为您提供了一个关于如何在 CHS SDK 中配置和使用 `MPControlAgent` 的坚实起点。您可以调整参数（如 `prediction_horizon`、`Q` 和 `R` 权重）以微调其性能来满足您的特定需求。
