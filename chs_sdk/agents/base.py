from typing import Any, Dict, Optional
import time


class Message:
    """
    Represents a message passed between agents on the message bus.
    """
    def __init__(self, topic: str, sender_id: str, payload: Dict[str, Any]):
        self.topic = topic
        self.sender_id = sender_id
        self.payload = payload
        self.timestamp = time.time()

    def __repr__(self):
        return f"Message(topic='{self.topic}', sender_id='{self.sender_id}', payload={self.payload})"


class BaseAgent:
    """
    The base class for all agents in the CHS-SDK.
    It defines the core interface for agent interaction with the message bus.
    """
    def __init__(self, agent_id: str, message_bus: Optional[Any] = None):
        self.agent_id = agent_id
        self.message_bus = message_bus

    def execute(self):
        """
        The main logic loop of the agent. This method is called periodically.
        It should contain the agent's primary function, such as running a model,
        performing a calculation, or sensing the environment.
        """
        raise NotImplementedError

    def on_message(self, message: Message):
        """
        A callback method that is triggered when an agent receives a message
        it has subscribed to.
        """
        raise NotImplementedError

    def publish(self, topic: str, payload: Dict[str, Any]):
        """
        Publishes a message to a specific topic on the message bus.
        """
        if self.message_bus:
            message = Message(topic=topic, sender_id=self.agent_id, payload=payload)
            self.message_bus.publish(message)
        else:
            print(f"Warning: Agent {self.agent_id} tried to publish but has no message bus.")

    def subscribe(self, topic: str):
        """
        Subscribes the agent to a specific topic on the message bus.
        """
        if self.message_bus:
            self.message_bus.subscribe(topic, self)
        else:
            print(f"Warning: Agent {self.agent_id} tried to subscribe but has no message bus.")
