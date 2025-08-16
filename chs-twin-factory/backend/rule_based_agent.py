from chs_sdk.agents.base import BaseAgent
from chs_sdk.agents.message import Message
from chs_sdk.utils.logger import log

class RuleBasedAgent(BaseAgent):
    """
    A simple rule-based control agent.
    It controls a gate based on a reservoir's water level.
    """
    def __init__(self, agent_id, kernel, level_topic, gate_topic, set_point, threshold=0.1, **kwargs):
        """
        Initializes the RuleBasedAgent.

        Args:
            agent_id (str): The unique identifier for the agent.
            kernel (AgentKernel): The agent kernel instance.
            level_topic (str): The topic to listen for water level updates.
            gate_topic (str): The topic to publish gate control commands to.
            set_point (float): The target water level.
            threshold (float): The deadband around the setpoint.
        """
        super().__init__(agent_id, kernel, **kwargs)
        self.level_topic = level_topic
        self.gate_topic = gate_topic
        self.set_point = set_point
        self.threshold = threshold
        self.current_level = 0.0
        self.initialized = False

    def setup(self):
        """
        Subscribes to the water level topic.
        """
        self.kernel.message_bus.subscribe(self, self.level_topic)

    def on_message(self, message: Message):
        """
        Handles incoming water level messages.
        """
        if message.topic == self.level_topic:
            # Assumes the payload has a 'level' key
            self.current_level = message.payload.get("level", 0.0)
            if not self.initialized:
                self.initialized = True
                log.info(f"RuleBasedAgent '{self.agent_id}' initialized with level: {self.current_level}")

    def execute(self, current_time: float):
        """
        Executes the control logic.
        """
        if not self.initialized:
            return

        # Simple rule: if level is above setpoint, open gate; otherwise, close it.
        if self.current_level > self.set_point + self.threshold:
            gate_opening = 1.0  # Open the gate
        else:
            gate_opening = 0.0  # Close the gate

        # Publish the control action for the gate
        self._publish(self.gate_topic, {"value": gate_opening})
