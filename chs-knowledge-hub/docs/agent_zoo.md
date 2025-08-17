---
tags:
  - 智能体
  - 模型
---

# 智能体动物园 (Agent Zoo)

欢迎来到智能体动物园！在这里，我们展示了一系列预先训练好的、可直接用于 `chs-sdk` 的高级智能体。您可以下载这些 `.agent` 文件，并将它们加载到您的项目中，以快速体验和集成强大的决策能力。

每个智能体都经过精心设计和测试，代表了解决特定问题的先进方法。

---

## 1. 模型预测控制智能体 (MPC Agent)

该智能体使用模型预测控制 (MPC) 来优化一个系统的性能，同时满足其物理约束。它非常适合用于需要精确控制和前瞻性规划的场景，例如水库水位控制或能源调度。

- **文件名:** `mpc_controller_project.zip`
- **版本:** 1.0
- **核心类:** `MPControlAgent`
- **功能:** 维持单个变量（如水位、温度）在一个期望的设定点附近。
- **性能指标:**
  - **设定点跟踪误差:** < 2%
  - **约束违反率:** 0% (在正常操作条件下)
- **使用方法:**
  ```python
  from chs.host import Host

  # 加载智能体
  mpc_agent = Host.load_agent_from_file('path/to/mpc_controller.agent')

  # 设置目标
  mpc_agent.set_target([100.0])

  # 在您的仿真循环中使用
  action = mpc_agent.compute_action(current_state)
  ```
- **下载链接:** [mpc_controller_project.zip](./assets/agents/mpc_controller.zip)

---

## 2. 梯级水库调度智能体 (Cascade Reservoir Manager)

这个复杂的管理智能体被设计用来解决梯级水库的联合调度优化问题。它使用先进的优化算法来计算未来一段时间内的最优放水计划，以最大化整个系统的总发电量。

- **文件名:** `cascade_manager_project.zip`
- **版本:** 1.0
- **核心类:** `ManagementAgent`
- **功能:** 为多达5个串联水库生成24小时的发电和放水调度计划。
- **性能指标:**
  - **发电量提升:** 相较于孤立运行，平均提升 8-12%。
  - **计算时间:** < 5秒 (对于一个典型的双水库系统)
- **使用方法:**
  ```python
  from chs.host import Host

  # 加载智能体
  manager = Host.load_agent_from_file('path/to/cascade_manager.agent')

  # 传入系统中的水库对象
  manager.set_managed_reservoirs([res1, res2, res3])

  # 计算最优调度
  optimal_schedule = manager.optimize_schedule(horizon=24)
  ```
- **下载链接:** [cascade_manager_project.zip](./assets/agents/cascade_manager.zip)

---

*未来，我们将添加更多智能体，包括基于强化学习的自适应控制器和用于复杂网络协调的智能体。敬请期待！*
