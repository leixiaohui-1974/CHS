from __future__ import annotations
import logging
from typing import Any, Dict, List, TYPE_CHECKING

from ..agent.base_agent import BaseAgent

if TYPE_CHECKING:
    from ..agent.communication import MessageBus

logger = logging.getLogger(__name__)

class HumanAgent(BaseAgent):
    """
    An agent that represents a human operator in the loop (HITL).

    This agent subscribes to 'decision_request' topics on the message bus.
    When a request is received, it would typically be forwarded to a human-machine
    interface (HMI). The human's response would then be published back to the bus.
    This implementation is a placeholder for that interaction.
    """
    def __init__(self, id: str, message_bus: MessageBus, decision_topics: List[str], **kwargs):
        super().__init__(id=id, message_bus=message_bus, **kwargs)
        self.decision_topics = decision_topics
        self._pending_requests: List[Dict[str, Any]] = []

        for topic in self.decision_topics:
            self.message_bus.subscribe(topic, self.handle_decision_request)

        logger.info(f"HumanAgent '{self.id}' initialized and subscribed to {self.decision_topics}.")

    def handle_decision_request(self, request: Dict[str, Any]):
        """
        Callback for when a decision request is received from the message bus.
        In a real implementation, this would send the request to an HMI.
        """
        logger.info(f"HumanAgent '{self.id}' received a decision request: {request}")
        self._pending_requests.append(request)
        # In a real system, you would now emit this to a WebSocket.
        print(f"--- TO HMI (via HumanAgent '{self.id}'): Operator action required ---")
        print(f"    State: {request.get('state')}")
        print(f"    Options: {request.get('options')}")
        print(f"-----------------------------------------------------------------")

    def inject_decision(self, response_topic: str, decision: Dict[str, Any]):
        """
        Simulates receiving a decision from the HMI and publishes it to the bus.
        This method would be called by the server handling HMI communication.
        """
        logger.info(f"HumanAgent '{self.id}' is injecting decision: {decision} to topic '{response_topic}'")
        self.message_bus.publish(response_topic, decision, sender_id=self.id)
        # A more robust implementation would match the decision to a specific request.
        if self._pending_requests:
            self._pending_requests.pop(0) # Simple FIFO for this example

    def step(self, dt: float, **kwargs):
        """
        The HumanAgent's step is typically passive, as it's driven by external
        human actions. This could be used for timeouts on decisions if needed.
        """
        pass

    def get_state(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.__class__.__name__,
            "pending_requests_count": len(self._pending_requests),
            "pending_requests": self._pending_requests,
        }
