import time
from .base import BaseAgent, Message
from typing import Dict


class LifecycleManagerAgent(BaseAgent):
    """
    A prototype agent that monitors the lifecycle of other agents.
    It listens for heartbeats and raises alerts if an agent goes offline.
    """
    def __init__(self, agent_id, message_bus, heartbeat_topic="lifecycle/heartbeat",
                 alert_topic="lifecycle/alert", timeout=10):
        super().__init__(agent_id, message_bus)
        self.heartbeat_topic = heartbeat_topic
        self.alert_topic = alert_topic
        self.timeout = timeout
        self.last_heartbeat: Dict[str, float] = {}
        self.subscribe(self.heartbeat_topic)

    def execute(self, dt=1.0):
        """
        Checks for agents that have not sent a heartbeat recently.
        """
        current_time = time.time()
        for agent_id, last_seen in list(self.last_heartbeat.items()):
            if current_time - last_seen > self.timeout:
                alert_payload = {
                    "agent_id": agent_id,
                    "status": "offline",
                    "last_seen": last_seen
                }
                self.publish(self.alert_topic, alert_payload)
                print(f"Alert: Agent {agent_id} is offline!")
                # Remove from tracking to avoid repeated alerts
                del self.last_heartbeat[agent_id]


    def on_message(self, message: Message):
        """
        Handles incoming heartbeat messages.
        """
        if message.topic == self.heartbeat_topic:
            sender_id = message.sender_id
            self.last_heartbeat[sender_id] = time.time()
            print(f"Received heartbeat from {sender_id}")


# To make this agent useful, other agents would need a heartbeat mechanism.
# We can add a simple heartbeat function to the BaseAgent.

def add_heartbeat_to_base_agent():
    """
    This is a conceptual demonstration. In a real scenario, you would modify
    the BaseAgent class directly.
    """
    def heartbeat(self):
        self.publish("lifecycle/heartbeat", {"status": "online"})

    # Add the heartbeat method to the BaseAgent class
    setattr(BaseAgent, 'heartbeat', heartbeat)

# You could call this function once at the start of your application
# to patch the BaseAgent class.
# add_heartbeat_to_base_agent()
