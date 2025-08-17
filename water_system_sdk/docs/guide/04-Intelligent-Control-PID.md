# 第四章：引入智能控制 - PID

在上一章中，我们模拟了一个具有恒定入流的水库。这被称为“开环”系统，因为没有反馈来控制结果。

在本章中，我们将“闭合回路”。我们将引入一个 **PID控制器智能体** 来自动调节水库的入流，以维持一个期望的水位，即 **设定值 (setpoint)**。这是您进入 `chs-sdk` “智能体版”世界的第一步。

## 什么是PID控制器？

PID（比例-积分-微分）控制器是工业界最常用的控制算法之一。它持续计算期望设定值与测量过程变量之间的“误差”值，并基于比例、积分和微分项应用校正。

*   **比例 (P)**: 对当前误差做出反应。误差越大，校正量越大。
*   **积分 (I)**: 考虑过去误差的累积。这有助于消除稳态误差。
*   **微分 (D)**: 响应误差的变化速率。这有助于抑制振荡。

如果这听起来很复杂，别担心。`chs-sdk` 提供了一个即用型的 `PIDController` 智能体，它为我们处理了所有的数学运算。

## 场景：维持水库水位

我们的目标是修改上一章的仿真。我们将用一个可控的入流代替恒定的入流。一个PID控制器将观察水库的水位，并调节入流以将水位保持在15个单位的设定值。

## 修改仿真脚本

让我们修改我们的 `run_reservoir_sim.py` 脚本。

### 第一步：导入 PIDController

首先，我们需要导入 `PIDController` 类。

```python
# 在之前的导入基础上增加
from chs_sdk.modules.control.pid_controller import PIDController
```

### 第二步：创建PID控制器智能体

现在，让我们创建一个 `PIDController` 的实例。我们需要为它提供P、I和D的调整参数（`kp`, `ki`, `kd`）以及我们期望的 `setpoint`。

```python
# 创建PID控制器智能体
pid_agent = PIDController(
    name='MyPIDController',
    kp=1.5,
    ki=0.1,
    kd=0.5,
    setpoint=15.0  # 我们的目标水位
)
```
为 `kp`, `ki`, `kd` 找到合适的值被称为“整定”，这是控制工程中的一个关键部分。目前，我们将使用这些示例值。

### 第三步：更新连接

这是最重要的部分。我们需要将我们的新控制器接入系统。

1.  PID控制器需要 **知道水库的当前水位**。因此，我们将水库的输出连接到控制器的输入。
2.  PID控制器将 **计算所需的入流**。因此，我们将控制器的输出连接到水库的入流输入。

我们旧的 `inflow_agent` 不再需要了，因为现在由PID控制器负责入流。

```python
# Host 和 Reservoir 的创建方式同前...

# 将智能体添加到主机
host.add_agent(reservoir_agent)
host.add_agent(pid_agent)

# --- 新的连接 ---
# 1. 将水库的水位连接到PID的测量值输入
host.add_connection(
    source_agent_name='MyReservoir',
    target_agent_name='MyPIDController',
    source_port_name='value',
    target_port_name='measured_value'
)

# 2. 将PID的输出连接到水库的入流
host.add_connection(
    source_agent_name='MyPIDController',
    target_agent_name='MyReservoir',
    source_port_name='output',
    target_port_name='inflow'
)
```

### 第四步：更新绘图代码

让我们更新我们的绘图代码，以同时显示设定值和控制器的输出（它指令的入流）。

```python
# 获取结果
results_df = host.get_datalogger().get_as_dataframe()

# 绘制结果
plt.figure(figsize=(12, 8))

# 图1：水库蓄水量
plt.subplot(2, 1, 1)
plt.plot(results_df.index, results_df['MyReservoir.value'], label='水库蓄水量')
# 添加一条设定值水平线
plt.axhline(y=15.0, color='r', linestyle='--', label='设定值 (15.0)')
plt.title('水库蓄水水位')
plt.ylabel('蓄水量 (单位)')
plt.legend()
plt.grid(True)

# 图2：控制器输出
plt.subplot(2, 1, 2)
plt.plot(results_df.index, results_df['MyPIDController.output'], label='PID 输出 (入流量)')
plt.title('控制器输出')
plt.ylabel('流量 (单位)')
plt.xlabel('时间 (小时)')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()
```

## 完整脚本与运行

本章的完整示例代码已保存到以下文件中：

`source/ch04/ch04_pid_control.py`

您可以直接运行此文件来查看仿真结果：

```bash
python water_system_sdk/docs/guide/source/ch04/ch04_pid_control.py
```

当您运行此脚本时，您将看到PID控制器在行动。水位将从10开始，控制器将指令一个高入流量以提高水位。当水位接近15的设定值时，控制器将减少入流，并最终稳定在一个能将水位保持在设定值的入流速率上。

您现在已经成功地使用一个智能体来控制一个仿真了！在接下来的章节中，我们将探索更高级的控制方法以及如何构建更复杂的系统模型。
