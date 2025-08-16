# 高级教程：构建多智能体协同系统

## 介绍

在复杂的系统中，多个智能体常常需要协同工作以实现全局目标。CHS SDK 通过 `MessageBus` 促进了这种协调，它允许智能体之间进行异步通信。

本教程将演示如何使用 `MessageBus` 来实现两个智能体——一个上游水库和一个下游水库——之间的简单协调。

## 场景

我们有两个水库，一个上游，一个下游。上游水库的放水将成为下游水库的入流。上游智能体的目标是维持其水位，而下游智能体需要根据上游的放水计划来调整自己的操作。

## 使用 `MessageBus`

`MessageBus` 作为一个中心化的消息代理。智能体可以向特定的“主题”发布消息，也可以订阅主题以接收消息。

### 1. 定义智能体

我们将创建两个智能体类：`UpstreamReservoirAgent` 和 `DownstreamReservoirAgent`。

#### 上游智能体

这个智能体将根据自身水位决定放水量，并将其计划发布到一个名为 `upstream_releases` 的主题。

```python
class UpstreamReservoirAgent:
    def __init__(self, agent_id, message_bus):
        self.agent_id = agent_id
        self.message_bus = message_bus
        self.water_level = 100.0 # 初始水位

    def step(self):
        # 决定放水量（一个简单的规则）
        if self.water_level > 105.0:
            release = 20.0
        elif self.water_level < 95.0:
            release = 5.0
        else:
            release = 10.0

        # 发布放水计划
        message = {'agent_id': self.agent_id, 'release_volume': release}
        self.message_bus.publish('upstream_releases', message)

        print(f"[{self.agent_id}] 水位: {self.water_level:.2f}, 放水: {release:.2f}")

        # 模拟自身水位变化（简化）
        self.water_level -= release * 0.1
```

#### 下游智能体

这个智能体订阅 `upstream_releases` 主题。当它收到消息时，它会将其用作其入流的一部分来更新自己的状态。

```python
class DownstreamReservoirAgent:
    def __init__(self, agent_id, message_bus):
        self.agent_id = agent_id
        self.message_bus = message_bus
        self.water_level = 80.0 # 初始水位
        self.upstream_release = 0.0

        # 订阅上游的放水主题
        self.message_bus.subscribe('upstream_releases', self.handle_upstream_release)

    def handle_upstream_release(self, message):
        """回调函数，用于处理来自上游的消息"""
        print(f"[{self.agent_id}] 收到消息: {message}")
        self.upstream_release = message['release_volume']

    def step(self):
        # 根据上游的放水更新自己的水位
        inflow = self.upstream_release
        self.water_level += inflow * 0.1 # 再次简化

        print(f"[{self.agent_id}] 水位: {self.water_level:.2f}, 收到上游入流: {self.upstream_release:.2f}")

```

### 2. 设置仿真

现在，我们实例化 `MessageBus` 和我们的智能体，并运行一个仿真循环。

```python
from chs.bus import MessageBus

# 1. 初始化 MessageBus
bus = MessageBus()

# 2. 创建智能体实例
upstream_agent = UpstreamReservoirAgent("upstream_res", bus)
downstream_agent = DownstreamReservoirAgent("downstream_res", bus)

# 3. 运行仿真
for t in range(5):
    print(f"\n--- 时间步 {t+1} ---")
    # 在每个步骤中，两个智能体都执行其逻辑
    upstream_agent.step()
    downstream_agent.step()

```

### 完整代码示例

为了使其可独立运行，我们将包含一个 `MessageBus` 的模拟实现。

```python
import collections

class MessageBus:
    """一个简单的 MessageBus 模拟实现"""
    def __init__(self):
        self.topics = collections.defaultdict(list)
        print("MessageBus 已初始化。")

    def subscribe(self, topic, callback):
        self.topics[topic].append(callback)

    def publish(self, topic, message):
        if topic in self.topics:
            for callback in self.topics[topic]:
                callback(message)

class UpstreamReservoirAgent:
    def __init__(self, agent_id, message_bus):
        self.agent_id = agent_id
        self.message_bus = message_bus
        self.water_level = 100.0

    def step(self):
        if self.water_level > 102.0:
            release = 15.0
        else:
            release = 10.0

        message = {'agent_id': self.agent_id, 'release_volume': release}
        self.message_bus.publish('upstream_releases', message)

        print(f"[{self.agent_id}] 水位: {self.water_level:.2f}, 发布放水计划: {release:.2f}")
        self.water_level += 5.0 - release # 假设有恒定的5单位入流

class DownstreamReservoirAgent:
    def __init__(self, agent_id, message_bus):
        self.agent_id = agent_id
        self.message_bus = message_bus
        self.water_level = 80.0
        self.upstream_release = 0.0
        self.message_bus.subscribe('upstream_releases', self.handle_upstream_release)

    def handle_upstream_release(self, message):
        # print(f"[{self.agent_id}] 收到消息: {message}")
        self.upstream_release = message['release_volume']

    def step(self):
        inflow = self.upstream_release
        print(f"[{self.agent_id}] 水位: {self.water_level:.2f}, 根据收到的 {inflow:.2f} m³/s 更新")
        self.water_level += (inflow - 5.0) * 0.2 # 假设自身有5单位的放水

# --- 仿真 ---
bus = MessageBus()
upstream_agent = UpstreamReservoirAgent("upstream_res", bus)
downstream_agent = DownstreamReservoirAgent("downstream_res", bus)

for t in range(5):
    print(f"\n--- 时间步 {t+1} ---")
    upstream_agent.step()
    downstream_agent.step()
```

这个例子展示了 `MessageBus` 的核心功能：解耦智能体。上游智能体不需要知道任何关于下游智能体的信息，反之亦然。它们只通过商定的消息格式和主题进行交互，这使得构建模块化和可扩展的多智能体系统成为可能。
