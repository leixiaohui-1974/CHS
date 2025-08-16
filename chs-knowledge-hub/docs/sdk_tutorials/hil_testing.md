# 高级教程：设置硬件在环(HIL)测试

## 介绍

硬件在环 (HIL) 测试是验证控制策略的关键一步。它允许您将 `chs-sdk` 中开发的智能体与真实或模拟的硬件连接起来，以在部署前测试其性能。

CHS SDK 通过 `HardwareProxy` 智能体简化了这一过程，`HardwareProxy` 可以与通过 MQTT 协议通信的硬件设备进行交互。本教程将指导您如何配置 `HardwareProxy` 并与一个模拟的 MQTT 硬件进行联调。

## 什么是 `HardwareProxy`?

`HardwareProxy` 作为一个桥梁，连接了 CHS 仿真环境和外部硬件。
- 它订阅来自 CHS 环境（例如，来自另一个智能体）的动作指令。
- 它将这些指令通过 MQTT 发送给硬件。
- 它订阅来自硬件的 MQTT 主题以接收状态更新。
- 它将这些状态更新发布回 CHS 环境的 `MessageBus`。

## HIL 设置

### 1. 模拟 MQTT 硬件

首先，我们需要一个模拟的硬件设备，它能连接到 MQTT 代理并与我们的 `HardwareProxy` 通信。我们将使用 `paho-mqtt` Python 库来创建一个简单的模拟水泵。

这个模拟水泵将：
- 订阅 `hardware/pump/control` 主题以接收指令（例如，`{"speed": 50}`)。
- 将其当前状态（例如，`{"rpm": 50, "flow_rate": 12.5}`) 发布到 `hardware/pump/state` 主题。

**模拟硬件脚本 (`mock_pump.py`)**

```python
import paho.mqtt.client as mqtt
import json
import time

MQTT_BROKER = "mqtt.eclipseprojects.io" # 使用一个公共的 MQTT 代理
MQTT_PORT = 1883

class MockPump:
    def __init__(self):
        self.rpm = 0
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "mock-pump")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(MQTT_BROKER, MQTT_PORT, 60)

    def on_connect(self, client, userdata, flags, rc, properties):
        print("已连接到 MQTT 代理。")
        # 订阅控制主题
        client.subscribe("hardware/pump/control")
        print("已订阅: hardware/pump/control")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload)
            print(f"收到指令: {payload}")
            if 'speed' in payload:
                # 根据指令更新状态
                self.rpm = payload['speed']
        except json.JSONDecodeError:
            print("无法解析收到的消息。")

    def publish_state(self):
        # 状态与 RPM 成正比
        flow_rate = self.rpm * 0.25
        state = {"rpm": self.rpm, "flow_rate": flow_rate}
        self.client.publish("hardware/pump/state", json.dumps(state))
        print(f"已发布状态: {state}")

    def run(self):
        self.client.loop_start()
        while True:
            self.publish_state()
            time.sleep(5) # 每5秒发布一次状态

if __name__ == "__main__":
    pump = MockPump()
    pump.run()
```
*要运行此脚本，您需要安装 `paho-mqtt`: `pip install paho-mqtt`*

### 2. 配置 `HardwareProxy`

现在，在您的 CHS 项目中，配置 `HardwareProxy` 以与模拟的水泵通信。

```python
from chs.agent import HardwareProxy
from chs.bus import MessageBus

# MQTT 和 MessageBus 的配置
proxy_config = {
    'agent_id': "pump_proxy",
    'mqtt_broker': "mqtt.eclipseprojects.io",
    'mqtt_port': 1883,
    # 定义动作到 MQTT 主题的映射
    'action_to_topic_map': {
        'pump_speed': 'hardware/pump/control'
    },
    # 定义 MQTT 主题到状态的映射
    'topic_to_state_map': {
        'hardware/pump/state': 'pump_state'
    },
    'message_bus': MessageBus() # 传入一个 MessageBus 实例
}

# 创建 HardwareProxy
hw_proxy = HardwareProxy(**proxy_config)
```
`action_to_topic_map` 告诉代理：当在 `MessageBus` 上收到一个键为 `pump_speed` 的动作时，应将其值发布到 `hardware/pump/control` MQTT 主题。
`topic_to_state_map` 告诉代理：当从 `hardware/pump/state` MQTT 主题收到消息时，应将其内容作为 `pump_state` 发布到 `MessageBus`。

### 3. 运行 HIL 仿真

现在，我们可以编写一个简单的脚本来模拟一个“控制智能体”，它向 `HardwareProxy` 发送指令。

```python
# 这是一个模拟的控制智能体，它决定水泵的速度
class ControlAgent:
    def __init__(self, agent_id, bus):
        self.agent_id = agent_id
        self.bus = bus
        # 订阅来自代理的状态更新
        self.bus.subscribe('pump_state', self.on_state_update)

    def on_state_update(self, state):
        print(f"[{self.agent_id}] 收到水泵状态: {state}")

    def set_pump_speed(self, speed):
        action = {'pump_speed': {'speed': speed}} # 嵌套的JSON结构
        self.bus.publish('agent_actions', action)
        print(f"[{self.agent_id}] 已发送指令设置速度为 {speed}")

# --- HIL 仿真 ---

# 1. 运行 `mock_pump.py` 脚本 (在另一个终端中)
# python mock_pump.py

# 2. 在您的主脚本中运行以下代码
bus = MessageBus()

proxy_config['message_bus'] = bus
hw_proxy = HardwareProxy(**proxy_config) # 假设 HardwareProxy 会自动连接

controller = ControlAgent("controller", bus)

print("\n--- HIL 测试开始 ---")

# 模拟发送一个指令
controller.set_pump_speed(75)

# 在一个真实的场景中，您会有一个运行循环
# time.sleep(10) # 等待状态消息返回

# 您应该会在 `mock_pump.py` 的终端中看到收到的指令，
# 并在您的主脚本终端中看到来自 `ControlAgent` 的状态更新回显。
```

这个设置创建了一个完整的回路：
1. `ControlAgent` -> `MessageBus` (动作)
2. `MessageBus` -> `HardwareProxy` (动作)
3. `HardwareProxy` -> MQTT (指令)
4. MQTT -> `MockPump` (指令)
5. `MockPump` -> MQTT (状态)
6. MQTT -> `HardwareProxy` (状态)
7. `HardwareProxy` -> `MessageBus` (状态)
8. `MessageBus` -> `ControlAgent` (状态)

这使得您可以将在纯软件仿真中开发的 `ControlAgent` 无缝地用于测试真实或模拟的硬件，这是迈向实际部署的重要一步。
