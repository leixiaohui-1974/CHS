# 第五章：高级控制 - 模型预测控制 (MPC)

在上一章中，我们使用PID控制器成功地控制了水库的水位。PID是一种强大且简单的“反应式”控制器。然而，在更复杂的系统中，我们可能需要一种更具“前瞻性”的控制策略。

本章将介绍 **模型预测控制 (Model Predictive Control, MPC)**，这是一种更先进的控制方法，它使用系统的数学模型来预测未来并做出最优决策。

## MPC 与 PID 有何不同？

*   **PID (反应式)**: PID控制器根据 *当前* 的误差（设定值与测量值之差）来计算控制动作。它对正在发生的事情做出反应。
*   **MPC (预测式)**: MPC控制器使用系统的模型来 *预测* 未来几个时间步内系统的行为。它会求解一个优化问题，以找到一系列能使未来输出最接近设定值的控制动作，同时满足各种约束（如最小/最大流量）。然后，它只执行这一系列动作中的第一个，并在下一个时间步重复整个过程。

**MPC的主要优势**:
*   **前瞻性**: 它可以预见并应对未来的扰动（如预报的入库流量）。
*   **处理约束**: 它可以显式地处理物理约束（例如，水泵的最高流量或水库的最高水位）。
*   **多变量控制**: 它天生适合控制具有多个输入和多个输出的复杂系统。

## 场景：使用MPC控制水库

我们的目标与上一章相同：将水库水位维持在15个单位的设定值。但这次，我们将使用 `MPCController` 来实现。

## 构建MPC仿真脚本

我们将修改之前的脚本。

### 第一步：导入 MPCController

我们需要 `MPCController` 和我们将用于预测的内部模型。

```python
# 在之前的导入基础上增加
from chs_sdk.modules.control.mpc_controller import MPCController
from chs_sdk.modules.modeling.storage_models import FirstOrderStorageModel
```

### 第二步：创建MPC控制器智能体

创建 `MPCController` 比PID要复杂一些，因为它需要一个内部的 **预测模型**。这个模型应该能很好地代表我们想要控制的真实系统（在我们的例子中，是 `reservoir_agent`）。

```python
# 1. 为MPC创建一个内部预测模型
# 这个模型应该与我们的“真实”水库模型相匹配
prediction_model_for_mpc = FirstOrderStorageModel(
    name='InternalPredictionModel',
    initial_value=10.0,
    time_constant=5.0
)

# 2. 创建MPC控制器智能体
mpc_agent = MPCController(
    name='MyMPCController',
    prediction_model=prediction_model_for_mpc,
    prediction_horizon=10,  # (P) 预测未来10个时间步
    control_horizon=3,     # (M) 优化未来3个控制动作
    set_point=15.0,        # 目标水位
    q_weight=1.0,          # 对跟踪误差的权重
    r_weight=0.1,          # 对控制力度的权重
    u_min=0.0,             # 控制动作（入流）的最小值
    u_max=20.0             # 控制动作（入流）的最大值
)
```

### 第三步：连接组件

接线方式与PID控制器非常相似。MPC控制器需要知道当前的水位，并且它的输出将驱动水库的入流。

```python
# Host 和 Reservoir 的创建方式同前...

# 添加智能体到主机
host.add_agent(reservoir_agent)
host.add_agent(mpc_agent)

# 1. 将水库的水位连接到MPC的测量值输入
host.add_connection(
    source_agent_name='MyReservoir',
    target_agent_name='MyMPCController',
    source_port_name='value',
    target_port_name='current_state' # 注意端口名称是 current_state
)

# 2. 将MPC的输出连接到水库的入流
host.add_connection(
    source_agent_name='MyMPCController',
    target_agent_name='MyReservoir',
    source_port_name='output',
    target_port_name='inflow'
)
```

### 第四步：更新绘图代码

绘图代码与PID示例几乎完全相同，我们只需要将 `MyPIDController` 替换为 `MyMPCController`。

## 完整脚本与运行

本章的完整示例代码已保存到以下文件中：

`source/ch05/ch05_mpc_control.py`

您可以直接运行此文件来查看仿真结果：

```bash
python water_system_sdk/docs/guide/source/ch05/ch05_mpc_control.py
```

当您运行此脚本时，您会看到与PID类似但可能更平滑的响应。MPC控制器正在“思考未来”，以一种优化的方式将水位驱动到设定值。

您现在已经了解了如何使用 `chs-sdk` 中更高级的控制策略。在后续章节中，我们将开始构建更复杂的、由多个相互连接的组件构成的水系统。
