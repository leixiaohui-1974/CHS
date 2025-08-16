from __future__ import annotations
import collections
from typing import Any, Callable, Dict, List, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class MessageBus:
    """
    A simple message bus for inter-agent communication.

    Allows agents to subscribe to topics and publish messages to topics. It also
    serves as a registry for all agents in the simulation.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = collections.defaultdict(list)
        self._agent_registry: Dict[str, BaseAgent] = {}

    def register_agent(self, agent: BaseAgent):
        """
        Registers an agent with the message bus, allowing it to be looked up by its ID.
        """
        if agent.id in self._agent_registry:
            raise ValueError(f"Agent with ID '{agent.id}' is already registered.")
        self._agent_registry[agent.id] = agent
        logger.info(f"Agent '{agent.id}' registered with the message bus.")

    def get_agent(self, agent_id: str) -> BaseAgent | None:
        """
        Retrieves a registered agent by its ID.
        """
        return self._agent_registry.get(agent_id)

    def subscribe(self, topic: str, callback: Callable[[Any], None]):
        """
        Subscribes a callback function to a specific topic.

        Args:
            topic: The topic to subscribe to.
            callback: The function to call when a message is published to the topic.
        """
        logger.debug(f"New subscription to topic '{topic}'.")
        self._subscribers[topic].append(callback)

    def unsubscribe(self, topic: str, callback: Callable[[Any], None]):
        """
        Unsubscribes a callback function from a topic.
        """
        if topic in self._subscribers:
            try:
                self._subscribers[topic].remove(callback)
                logger.debug(f"Unsubscribed from topic '{topic}'.")
            except ValueError:
                logger.warning(f"Attempted to unsubscribe a non-existent callback from topic '{topic}'.")
                pass

    def publish(self, topic: str, message: Any, sender_id: str = "System"):
        """
        Publishes a message to all subscribers of a topic.

        Args:
            topic: The topic to publish the message to.
            message: The message to send.
            sender_id: The ID of the agent sending the message.
        """
        logger.debug(f"Publishing message on topic '{topic}' from sender '{sender_id}'.")
        if topic in self._subscribers:
            # Iterate over a copy of the list in case a callback modifies the subscriber list
            for callback in self._subscribers[topic][:]:
                try:
                    callback(message)
                except Exception as e:
                    logger.error(f"Error in subscriber for topic '{topic}': {e}", exc_info=True)
