# 第三十二章：高级主题 (4) - SDK与外部系统集成

欢迎来到本指南的最后一章。至此，我们已经学习了如何构建从简单到复杂的各类水务仿真模型。但要让仿真系统真正发挥价值，它必须能够与外部世界进行交互，接收真实世界的数据，并可能反向控制真实的硬件。这就是 **数字孪生 (Digital Twin)** 和 **硬件在环 (Hardware-in-the-Loop, HIL)** 仿真的核心。

`chs-sdk` 通过 `MqttHardwareProxy` 智能体，提供了一个与外部系统连接的标准接口。

## 核心概念：硬件代理 (Hardware Proxy)

`MqttHardwareProxy` 扮演了一个“翻译官”或“桥梁”的角色。它连接着两个不同的通信世界：
1.  **内部世界**: `chs-sdk` 仿真环境内部的消息总线 (Message Bus)。
2.  **外部世界**: 一个外部的 **MQTT Broker**。MQTT是一种轻量级的、广泛应用于物联网(IoT)的消息协议。

这个代理的工作是双向的：
*   **指令下发 (Command Out)**: 它监听内部的一个特定主题（例如 `hardware.command.pump1`）。当仿真中的某个决策智能体（如`DispatchAgent`）向这个主题发布一条指令时，`MqttHardwareProxy` 会接收到该指令，并将其转发到外部MQTT Broker的一个对应主题上（例如 `chs/hil/pump1/command`）。
*   **状态上报 (State In)**: 同时，它也监听外部MQTT Broker上的一个主题（例如 `chs/hil/pump1/state`）。当一个真实的硬件设备（或模拟它的脚本）向这个主题发布其状态时，`MqttHardwareProxy` 会接收到该状态，并将其转发到内部消息总线的一个对应主题上（例如 `hardware.state.pump1`），供仿真系统中的其他智能体使用。

通过这个桥梁，仿真模型就“活”了起来，它能感知真实硬件的状态，并能向其发送控制指令。

## 场景：硬件在环控制一个真实的水泵

由于我们无法在这里搭建一个真实的MQTT Broker和硬件，本章将通过两个概念性的代码片段，来展示这个工作流程。

*   **场景**: 仿真系统需要控制一个“真实”的水泵。一个`DispatchAgent`将决定水泵的开关，并需要读取水泵的实际运行状态。
*   **目标**: 理解 `MqttHardwareProxy` 如何实现仿真世界与现实世界的解耦和通信。

## 构建集成系统

### 1. 仿真系统侧 (`ch32_simulation_side.py`)

在 `chs-sdk` 的仿真脚本中，我们需要做的是：
1.  实例化 `MqttHardwareProxy`，并告诉它MQTT服务器的地址和要代理的设备ID。
2.  实例化一个 `DispatchAgent`。
3.  在 `DispatchAgent` 的逻辑中，通过向 `hardware.command.pump1` 发布消息来控制水泵，并通过订阅 `hardware.state.pump1` 来获取其状态。

```python
# --- 仿真系统侧 (conceptual code) ---
from chs_sdk.core.host import Host
from chs_sdk.agents.dispatch_agent import DispatchAgent
from chs_sdk.interfaces.hardware_proxy import MqttHardwareProxy

def run_hil_simulation():
    host = Host()

    # 1. 创建硬件代理
    # 需要一个正在运行的MQTT Broker (例如, Mosquitto)
    proxy = MqttHardwareProxy(
        agent_id='PumpProxy',
        kernel=host,
        device_id='pump1',
        mqtt_broker='localhost', # MQTT服务器地址
        mqtt_port=1883
    )

    # 2. 创建一个简单的调度智能体
    class SimpleDispatcher(DispatchAgent):
        def setup(self):
            # 监听硬件的状态更新
            self.kernel.message_bus.subscribe(self, 'hardware.state.pump1')

        def execute(self, current_time, time_step):
            # 简单的逻辑：在第10秒时开启水泵
            if current_time > 10 and self.last_command_time < 10:
                print("[仿真] 发送开启指令到硬件...")
                self._publish('hardware.command.pump1', {'command': 'start'})
                self.last_command_time = current_time

        def on_message(self, message):
            if message.topic == 'hardware.state.pump1':
                print(f"[仿真] 收到硬件状态: {message.payload}")

    dispatcher = SimpleDispatcher('MyDispatcher', host)
    dispatcher.last_command_time = 0

    # 3. 运行
    host.add_agents([proxy, dispatcher])
    proxy.connect() # 连接到MQTT
    host.run(num_steps=30, dt=1.0)
    proxy.disconnect()

# if __name__ == "__main__":
#     run_hil_simulation()
```

### 2. 硬件/外部系统侧 (`ch32_hardware_side.py`)

这是一个独立的Python脚本，它模拟了真实的水泵硬件。它也连接到同一个MQTT Broker。

```python
# --- 硬件侧 (conceptual code) ---
import paho.mqtt.client as mqtt
import time
import json

DEVICE_ID = 'pump1'
BROKER = 'localhost'
PORT = 1883

# 硬件的当前状态
pump_state = {"status": "stopped", "flow": 0}

def on_connect(client, userdata, flags, rc):
    print("[硬件] 连接到MQTT Broker成功。")
    # 监听来自仿真的指令
    client.subscribe(f"chs/hil/{DEVICE_ID}/command")
    print(f"[硬件] 订阅了指令主题: chs/hil/{DEVICE_ID}/command")

def on_message(client, userdata, msg):
    # 当收到指令时
    payload = json.loads(msg.payload.decode())
    print(f"[硬件] 收到指令: {payload}")
    if payload.get('command') == 'start':
        pump_state['status'] = 'running'
        pump_state['flow'] = 25.0
    elif payload.get('command') == 'stop':
        pump_state['status'] = 'stopped'
        pump_state['flow'] = 0

def run_mock_hardware():
    client = mqtt.Client(client_id=f"mock_hardware_{DEVICE_ID}")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)

    # 硬件的主循环
    client.loop_start()
    try:
        while True:
            # 硬件定期发布自己的状态
            print(f"[硬件] 发布状态: {pump_state}")
            client.publish(f"chs/hil/{DEVICE_ID}/state", json.dumps(pump_state))
            time.sleep(5) # 每5秒上报一次状态
    except KeyboardInterrupt:
        print("[硬件] 停止运行。")
    client.loop_stop()
    client.disconnect()

# if __name__ == "__main__":
#     run_mock_hardware()
```

### 总结

通过 `MqttHardwareProxy`，我们将仿真系统与硬件（或其模拟脚本）完全解耦。仿真中的 `DispatchAgent` 只需与内部消息总线交互，而无需关心底层的通信协议。这使得 `chs-sdk` 可以灵活地嵌入到更广泛的工业物联网或实时控制平台中。

至此，本指南的所有核心章节都已完成。恭喜您，您已经从一位初学者，成长为能够应对复杂水务仿真挑战的 `chs-sdk` 专家！
