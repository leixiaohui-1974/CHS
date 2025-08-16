import logging

class FallbackAgent:
    """
    A simple, rule-based agent that provides a safe fallback action
    when the primary agent is unavailable or the system is offline.
    """
    def __init__(self):
        """Initializes the FallbackAgent."""
        self.agent_id = "fallback_agent_v1.0"
        logging.info(f"Initialized FallbackAgent: {self.agent_id}")

    def execute(self, observation: dict) -> dict:
        """
        Returns a predefined safe action, ignoring the observation.

        Args:
            observation: The current sensor readings (ignored).

        Returns:
            A dictionary representing a safe action.
        """
        logging.warning("Executing fallback action. System is in a safe state.")
        # This is a conservative, safe action.
        safe_action = {
            "gate_opening": 0.2,  # Fixed low opening
            "pump_status": 0        # Pumps off
        }
        return safe_action

    def update_parameters(self, params: dict):
        """
        This agent does not support parameter updates. This method is for
        interface compatibility.
        """
        logging.info("FallbackAgent does not support dynamic parameter updates.")
        pass
