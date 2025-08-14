from abc import ABC, abstractmethod
from collections import defaultdict
from typing import List, Dict

from .base_agent import BaseAgent
from .message import Message


class BaseMessageBus(ABC):
    """
    Abstract base class for a message bus.
    """

    @abstractmethod
    def publish(self, message: Message):
        """
        Publishes a message to the bus.
        """
        pass

    @abstractmethod
    def subscribe(self, agent: BaseAgent, topic: str):
        """
        Subscribes an agent to a topic.
        """
        pass

    @abstractmethod
    def dispatch(self):
        """
        Process and deliver any pending messages.
        The kernel calls this method in its main loop.
        """
        pass


class InMemoryMessageBus(BaseMessageBus):
    """
    An in-memory message bus for local development and testing.
    """

    def __init__(self):
        self._subscriptions: Dict[str, List[BaseAgent]] = defaultdict(list)
        self._message_queue: List[Message] = []

    def subscribe(self, agent: BaseAgent, topic: str):
        """
        Subscribes an agent to a topic.
        """
        if agent not in self._subscriptions[topic]:
            self._subscriptions[topic].append(agent)

    def publish(self, message: Message):
        """
        Adds a message to the internal queue for later dispatch.
        """
        self._message_queue.append(message)

    def dispatch(self):
        """
        Dispatches all messages in the queue to their subscribers.
        This method is called by the AgentKernel in its run loop.
        """
        q = self._message_queue
        self._message_queue = []
        for message in q:
            if message.topic in self._subscriptions:
                for subscriber in self._subscriptions[message.topic]:
                    # In a real scenario, this might be a non-blocking call
                    subscriber.on_message(message)
