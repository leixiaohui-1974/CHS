from typing import List, Dict
from ..utils.logger import log
from .base_agent import BaseAgent
from .message import Message

# --- Constants for topic names ---
TOPIC_CMD_LIFECYCLE_RESTART = "cmd.lifecycle.restart"
TOPIC_SYS_MONITORING_PERFORMANCE = "system.monitoring.performance"


class LifecycleManagerAgent(BaseAgent):
    """
    Manages the lifecycle of other agents, primarily by handling restart commands
    for agents that are in a FAULT state.
    """
    def setup(self):
        """
        Subscribes to the restart command topic during setup.
        """
        self.kernel.message_bus.subscribe(self, TOPIC_CMD_LIFECYCLE_RESTART)
        log.info(f"LifecycleManagerAgent '{self.agent_id}' is active and listening on '{TOPIC_CMD_LIFECYCLE_RESTART}'.")

    def execute(self, current_time: float):
        """
        The LifecycleManagerAgent is purely reactive, so it does nothing in its execute loop.
        """
        pass

    def on_message(self, message: Message):
        """
        Handles incoming command messages.
        """
        if message.topic == TOPIC_CMD_LIFECYCLE_RESTART:
            agent_to_restart = message.payload.get("agent_id")
            if not agent_to_restart:
                log.warning(f"Received restart command with no agent_id specified.")
                return

            log.info(f"Received command to restart agent: '{agent_to_restart}'")
            success = self.kernel.restart_agent(agent_to_restart)
            if success:
                log.info(f"Successfully initiated restart for agent '{agent_to_restart}'.")
            else:
                log.error(f"Failed to initiate restart for agent '{agent_to_restart}'.")

    def shutdown(self):
        log.info(f"LifecycleManagerAgent '{self.agent_id}' shutting down.")


class MonitoringAgent(BaseAgent):
    """
    Periodically collects performance metrics from the kernel and message bus
    and publishes them to a designated system topic.
    """
    def __init__(self, agent_id: str, kernel: 'AgentKernel', **config):
        super().__init__(agent_id, kernel, **config)
        self.publish_interval = config.get("publish_interval", 5.0) # Default to every 5 seconds
        self.last_publish_time = -1.0

    def setup(self):
        log.info(
            f"MonitoringAgent '{self.agent_id}' initialized. "
            f"Publishing metrics every {self.publish_interval} seconds to '{TOPIC_SYS_MONITORING_PERFORMANCE}'."
        )

    def execute(self, current_time: float):
        """
        Checks if it's time to publish a new performance report.
        """
        if current_time - self.last_publish_time >= self.publish_interval:
            self.last_publish_time = current_time
            self._collect_and_publish_metrics(current_time)

    def on_message(self, message: Message):
        """
        This agent does not subscribe to any topics.
        """
        pass

    def _collect_and_publish_metrics(self, current_time: float):
        """
        Gathers metrics from the kernel and message bus and publishes them.
        """
        # 1. Get agent execution times from the kernel
        agent_performance = self.kernel.get_agent_performance()

        # 2. Get topic queue lengths from the message bus
        try:
            # This assumes the message bus has the get_topic_queue_lengths method
            topic_queues = self.kernel.message_bus.get_topic_queue_lengths()
        except AttributeError:
            log.warning("Message bus does not support queue length monitoring.")
            topic_queues = {}

        # 3. Assemble the payload
        metrics_payload = {
            "timestamp": current_time,
            "agent_execution_times_sec": agent_performance,
            "topic_queue_lengths": topic_queues,
        }

        # 4. Publish the metrics
        self._publish(TOPIC_SYS_MONITORING_PERFORMANCE, metrics_payload)
        log.debug(f"Published performance metrics at time {current_time:.2f}.")

    def shutdown(self):
        log.info(f"MonitoringAgent '{self.agent_id}' shutting down.")


class DataLoggerAgent(BaseAgent):
    """
    A simple agent that logs all messages it receives to the console.
    """
    def __init__(self, agent_id: str, kernel: 'AgentKernel', **config):
        super().__init__(agent_id, kernel, **config)
        self.topics_to_log = config.get("topics_to_log", ["#"]) # Default to all topics

    def setup(self):
        """
        Subscribe to the specified topics.
        """
        for topic in self.topics_to_log:
            self.kernel.message_bus.subscribe(self, topic)
        log.info(f"DataLoggerAgent '{self.agent_id}' is active and logging topics: {self.topics_to_log}")

    def execute(self, current_time: float):
        """
        The DataLoggerAgent is purely reactive.
        """
        pass

    def on_message(self, message: Message):
        """
        Prints the received message to the console.
        """
        print(f"[Logger] Time: {self.kernel.current_time:.2f} | Topic: {message.topic} | Sender: {message.sender_id} | Payload: {message.payload}")


class DataCaptureAgent(BaseAgent):
    """
    An agent that captures messages from specified topics and stores them in memory.
    This is intended for use in automated workflows where simulation results need
    to be programmatically analyzed.
    """
    def __init__(self, agent_id: str, kernel: 'AgentKernel', **config):
        super().__init__(agent_id, kernel, **config)
        self.topics_to_log = config.get("topics_to_log", ["#"])  # Default to all topics
        self.data = []

    def setup(self):
        """
        Subscribe to the specified topics.
        """
        for topic in self.topics_to_log:
            self.kernel.message_bus.subscribe(self, topic)
        log.info(f"DataCaptureAgent '{self.agent_id}' is active and capturing topics: {self.topics_to_log}")

    def execute(self, current_time: float):
        """
        The DataCaptureAgent is purely reactive.
        """
        pass

    def on_message(self, message: Message):
        """
        Captures the received message and stores it in a list.
        """
        self.data.append({
            "time": self.kernel.current_time,
            "topic": message.topic,
            "sender_id": message.sender_id,
            "payload": message.payload
        })

    def get_data(self) -> List[Dict]:
        """
        Returns all captured data.
        """
        return self.data

    def clear_data(self):
        """
        Clears all captured data from memory.
        """
        self.data = []
