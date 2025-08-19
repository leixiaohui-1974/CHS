# Tutorial: Creating a Custom Agent

The CHS platform's agent-based architecture is designed for extensibility. You can create your own custom agents to perform specialized tasks like data logging, implementing unique control logic, or interfacing with external systems.

This tutorial will guide you through creating a simple yet practical `DataLoggerAgent`. This agent will:
1.  Subscribe to a specific message topic.
2.  Open a local file to write to.
3.  Write the payload of any message it receives to the file.
4.  Cleanly close the file when the simulation ends.

## 1. The Basic Agent Structure

All agents must inherit from the `BaseAgent` class, which provides the fundamental structure and lifecycle methods. Let's start by creating a new Python file for our agent, for example, `my_agents/data_logger.py`.

Here is the basic skeleton:

```python
# my_agents/data_logger.py
from chs_sdk.agents.base import BaseAgent
from chs_sdk.agents.message import Message
from chs_sdk.core.host import AgentKernel

class DataLoggerAgent(BaseAgent):
    """
    A simple agent that subscribes to a topic and logs message payloads to a file.
    """
    def __init__(self, agent_id: str, kernel: 'AgentKernel', **config):
        super().__init__(agent_id, kernel, **config)
        # We'll initialize our custom attributes here

    def setup(self):
        # One-time setup tasks go here
        pass

    def on_execute(self, current_time: float, time_step: float):
        # Logic to be executed at each time step
        pass

    def on_message(self, message: Message):
        # Logic to handle incoming messages
        pass

    def shutdown(self):
        # Cleanup tasks go here
        pass
```

## 2. Implementing the Lifecycle Methods

Now, let's fill in the methods to give our agent its functionality.

### `__init__` - Configuration

First, we need to configure our agent. It needs to know which topic to listen to and where to save the log file. We'll get this information from the `config` dictionary passed to the constructor.

```python
# In DataLoggerAgent class
def __init__(self, agent_id: str, kernel: 'AgentKernel', **config):
    super().__init__(agent_id, kernel, **config)
    self.topic_to_subscribe = config.get("topic", "default/topic")
    self.log_file_path = config.get("log_file", "datalog.txt")
    self._file_handle = None
```

### `setup` - Initialization

The `setup` method is called once by the `AgentKernel` before the simulation loop begins. This is the perfect place to subscribe to our topic and open the log file for writing.

```python
# In DataLoggerAgent class
def setup(self):
    print(f"[{self.agent_id}] Setting up. Subscribing to '{self.topic_to_subscribe}' and opening '{self.log_file_path}'.")
    self.kernel.message_bus.subscribe(self, self.topic_to_subscribe)
    try:
        self._file_handle = open(self.log_file_path, 'w')
    except IOError as e:
        print(f"[{self.agent_id}] Error opening file: {e}")
```

### `on_message` - Reacting to Data

The `on_message` method is called by the kernel whenever a message is published to a topic the agent is subscribed to. Here, we'll simply write the message payload to our file.

```python
# In DataLoggerAgent class
def on_message(self, message: Message):
    if self._file_handle:
        log_line = f"[{message.timestamp}] {message.payload}\n"
        self._file_handle.write(log_line)
```

### `on_execute` - The "Heartbeat"

Our agent is purely reactive and doesn't need to do anything on its own at each time step. So, we'll just leave the `on_execute` method empty.

```python
# In DataLoggerAgent class
def on_execute(self, current_time: float, time_step: float):
    # This agent is reactive, so it does nothing on its own.
    pass
```

### `shutdown` - Cleaning Up

The `shutdown` method is called once after the simulation loop finishes. It's crucial to perform cleanup tasks here, like closing our file handle to ensure all data is written to disk.

```python
# In DataLoggerAgent class
def shutdown(self):
    print(f"[{self.agent_id}] Shutting down. Closing file.")
    if self._file_handle:
        self._file_handle.close()
```

## 3. Running the Agent

To use our new agent, we need to add it to a simulation configuration file. The `SimulationManager` needs to know where to find the agent's class. You can do this by adding it to the `ComponentRegistry` or by providing the full import path in the config.

Assuming you have registered your agent in the `ComponentRegistry` with the key `"DataLoggerAgent"`, the configuration would look like this:

```yaml
# In your simulation_config.yaml

components:
  # ... other components like a disturbance agent that publishes data ...

  my_logger:
    type: DataLoggerAgent
    params:
      topic: "data/raw"
      log_file: "output/sensor_data.log"

execution_order:
  - # ... other components ...
  - my_logger
```

When you run a simulation with this configuration, the `DataLoggerAgent` will be created, it will listen for any messages on the `"data/raw"` topic, and it will write their payloads to `output/sensor_data.log`.

Congratulations! You've created a custom agent that extends the functionality of the CHS platform. You can use this same pattern to build agents with far more complex behaviors.
