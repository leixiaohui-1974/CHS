from abc import ABC, abstractmethod
from collections import defaultdict
from typing import List, Dict

from .base import BaseAgent
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


from ..utils.logger import log
from .agent_status import AgentStatus


class InMemoryMessageBus(BaseMessageBus):
    """
    An in-memory message bus for local development and testing.
    This version includes topic-based queues for monitoring and robust error handling.
    """

    def __init__(self):
        self._subscriptions: Dict[str, List[BaseAgent]] = defaultdict(list)
        self._message_queue: Dict[str, List[Message]] = defaultdict(list)

    def subscribe(self, agent: BaseAgent, topic: str):
        """
        Subscribes an agent to a topic.
        """
        if agent not in self._subscriptions[topic]:
            self._subscriptions[topic].append(agent)
            log.debug(f"Agent '{agent.agent_id}' subscribed to topic '{topic}'.")

    def publish(self, message: Message):
        """
        Adds a message to the internal queue for the specified topic.
        """
        self._message_queue[message.topic].append(message)
        log.trace(f"Message published to topic '{message.topic}' by '{message.sender_id}'.")

    def dispatch(self):
        """
        Dispatches all messages in the queue to their subscribers.
        If an agent fails to handle a message, it is marked as FAULT.
        """
        # Process all topics that have messages
        topics_to_process = list(self._message_queue.keys())
        for topic in topics_to_process:
            # Dispatch all messages for the current topic
            messages_to_dispatch = self._message_queue.pop(topic, [])
            if not messages_to_dispatch:
                continue

            # Get subscribers for the specific topic AND wildcard subscribers
            specific_subscribers = self._subscriptions.get(topic, [])
            wildcard_subscribers = self._subscriptions.get("#", [])
            subscribers = list(set(specific_subscribers + wildcard_subscribers)) # Use set to avoid duplicates

            if not subscribers:
                log.warning(f"No subscribers for topic '{topic}', {len(messages_to_dispatch)} messages discarded.")
                continue

            for message in messages_to_dispatch:
                for subscriber in subscribers:
                    try:
                        # Only deliver messages to running agents
                        if subscriber.status == AgentStatus.RUNNING:
                            subscriber.on_message(message)
                    except Exception as e:
                        subscriber.status = AgentStatus.FAULT
                        log.error(
                            f"Error processing message in agent '{subscriber.agent_id}' on topic '{topic}'. "
                            f"Agent set to FAULT. Error: {e}",
                            exc_info=True
                        )

    def get_topic_queue_lengths(self) -> Dict[str, int]:
        """
        Returns the current number of pending messages for each topic.
        """
        return {topic: len(queue) for topic, queue in self._message_queue.items()}
