# 第三章：您的第一个仿真 - 单个水库

在本章中，您将通过构建和运行一个单个水库的模型，来学习 `chs-sdk` 仿真引擎的基本概念。

## 核心概念

`chs-sdk` “核心版” 的核心是三个主要概念：

1.  **实体 (Entities)**: 这些是您水系统的物理组成部分，如水库、渠道、水泵和闸门。在SDK中，这些通常被表示为“智能体”(agents)。每个实体都有一个描述其行为的数学模型。
2.  **连接 (Connections)**: 它们定义了您的实体之间如何相互连接，从而创建了一个代表您完整水系统的网络。
3.  **主机 (Host)**: 这是驱动仿真的引擎。它管理仿真时间，在每个时间步长执行每个实体的模型，并收集结果。

## 场景：一个简单的水库

我们的目标是模拟一个具有以下特征的水库：

*   它有初始蓄水量。
*   它接收恒定的入流。
*   它有一个出口，出流量与水库中的水量成正比（这是一个简单的“线性水库”模型）。

我们希望观察水库的水位在24小时内如何变化。

## 构建仿真脚本

让我们编写一个Python脚本来构建和运行这个仿真。创建一个名为 `run_reservoir_sim.py` 的新文件。

### 第一步：导入必要的类

首先，我们需要从SDK中导入我们将要使用的类。

```python
import matplotlib.pyplot as plt

# Host 是主要的仿真环境
from chs_sdk.core.host import Host
# 这个智能体将代表我们的水库
from chs_sdk.modules.modeling.storage_models import FirstOrderStorageModel
# 这个智能体将提供一个恒定的入流
from chs_sdk.modules.disturbances.predefined import ConstantDisturbance
```

### 第二步：创建仿真主机

`Host` 是我们仿真环境的主要容器。

```python
# 创建一个仿真主机
host = Host()
```

### 第三步：定义水库模型

现在，让我们创建我们的水库。我们将使用 `FirstOrderStorageModel`。这是一个简单但常见的模型，其中出流量与蓄水量成正比。我们需要给它一个名称、一个初始蓄水量和一个决定其排水速度的 `time_constant`（时间常数）。

```python
# 创建水库模型智能体
reservoir_agent = FirstOrderStorageModel(
    name='MyReservoir',
    initial_value=10.0,  # 初始水量为 10 个单位
    time_constant=5.0  # 时间常数越大，排水越慢
)
```

### 第四步：定义扰动（入流）

我们的水库需要入流。我们将使用 `ConstantDisturbance` 类创建一个恒定为5个单位的入流。

```python
# 创建一个恒定入流扰动智能体
inflow_agent = ConstantDisturbance(
    name='inflow',
    constant_value=5.0
)
```

### 第五步：注册组件和连接

现在我们需要告诉 `Host` 我们的水库和入流。我们还需要定义它们是如何连接的。

```python
# 将智能体添加到主机
host.add_agent(reservoir_agent)
host.add_agent(inflow_agent)

# 将入流智能体的输出连接到水库智能体的入流输入
host.add_connection(
    source_agent_name='inflow',
    target_agent_name='MyReservoir',
    source_port_name='value',
    target_port_name='inflow'
)
```
这告诉仿真，在每个时间步，`inflow` 智能体的 `value`（值）应该输入到 `MyReservoir` 智能体的 `inflow`（入流）端口。

### 第六步：运行仿真

一切设置就绪后，我们现在可以运行仿真了。我们将运行24个时间步，每个步长代表1小时。

```python
# 运行仿真，共24步，步长为1小时
host.run(num_steps=24, dt=1.0)
```

### 第七步：可视化结果

`Host` 在仿真期间会自动记录所有组件的状态。我们可以将这些数据作为pandas DataFrame获取，并绘制图表以查看结果。

```python
# 从数据记录器获取结果
results_df = host.get_datalogger().get_as_dataframe()

# 绘制水库蓄水量随时间的变化
plt.figure(figsize=(10, 6))
plt.plot(results_df.index, results_df['MyReservoir.value'], label='水库蓄水量')
plt.xlabel('时间 (小时)')
plt.ylabel('蓄水量 (单位)')
plt.title('水库仿真结果')
plt.grid(True)
plt.legend()
plt.show()
```

## 完整脚本

这是完整的 `run_reservoir_sim.py` 脚本：

```python
import matplotlib.pyplot as plt

from chs_sdk.core.host import Host
from chs_sdk.modules.modeling.storage_models import FirstOrderStorageModel
from chs_sdk.modules.disturbances.predefined import ConstantDisturbance

# 1. 创建一个仿真主机
host = Host()

# 2. 定义水库模型智能体
reservoir_agent = FirstOrderStorageModel(
    name='MyReservoir',
    initial_value=10.0,
    time_constant=5.0
)

# 3. 定义一个恒定入流扰动智能体
inflow_agent = ConstantDisturbance(
    name='inflow',
    constant_value=5.0
)

# 4. 注册组件和连接
host.add_agent(reservoir_agent)
host.add_agent(inflow_agent)
host.add_connection(
    source_agent_name='inflow',
    target_agent_name='MyReservoir',
    source_port_name='value',
    target_port_name='inflow'
)

# 5. 运行仿真
host.run(num_steps=24, dt=1.0)

# 6. 可视化结果
results_df = host.get_datalogger().get_as_dataframe()
print("仿真结果:")
print(results_df)

plt.figure(figsize=(10, 6))
plt.plot(results_df.index, results_df['MyReservoir.value'], label='水库蓄水量')
plt.xlabel('时间 (小时)')
plt.ylabel('蓄水量 (单位)')
plt.title('水库仿真结果')
plt.grid(True)
plt.legend()
plt.show()

```

当您运行此脚本时，您应该会看到一个图表，显示水库的蓄水量从10个单位开始，并逐渐增加到一个稳定状态。

恭喜！您已经成功使用 `chs-sdk` 构建并运行了您的第一个仿真。在下一章中，我们将学习如何添加一个控制器来自动管理水库的水位。
