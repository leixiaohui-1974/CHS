import logging
import time
from datetime import datetime, timedelta

class SafetyWrapper:
    """
    A wrapper that enforces hardcoded safety rules on actions before they are executed.
    """
    def __init__(self, pump_cooldown_minutes: int = 5):
        """
        Initializes the SafetyWrapper.

        Args:
            pump_cooldown_minutes: The minimum time in minutes between pump activations.
        """
        self.last_pump_activation_time = None
        self.pump_cooldown = timedelta(minutes=pump_cooldown_minutes)
        logging.info(f"SafetyWrapper initialized with a pump cooldown of {pump_cooldown_minutes} minutes.")

    def validate_and_sanitize(self, action: dict) -> dict:
        """
        Validates an action against a set of safety rules and sanitizes it if necessary.

        Args:
            action: The action dictionary proposed by an agent.

        Returns:
            A sanitized action dictionary that is safe to execute.
        """
        if not isinstance(action, dict):
            logging.error(f"SafetyWrapper received an invalid action of type {type(action)}. Returning a safe default.")
            return self._get_safe_default()

        # Create a copy to avoid modifying the original action dict
        sanitized_action = action.copy()

        # Rule 1: Gate opening must be between 0.0 and 0.9
        if 'gate_opening' in sanitized_action:
            original_gate_opening = sanitized_action['gate_opening']
            sanitized_action['gate_opening'] = max(0.0, min(original_gate_opening, 0.9))
            if original_gate_opening != sanitized_action['gate_opening']:
                logging.warning(f"Sanitized gate_opening from {original_gate_opening} to {sanitized_action['gate_opening']}.")

        # Rule 2: Pump status must be 0 or 1
        if 'pump_status' in sanitized_action:
            original_pump_status = sanitized_action['pump_status']
            if sanitized_action['pump_status'] not in [0, 1]:
                logging.warning(f"Sanitized pump_status from '{original_pump_status}' to 0.")
                sanitized_action['pump_status'] = 0 # Default to off

            # Rule 3: Enforce pump cooldown period
            if sanitized_action['pump_status'] == 1:
                if self.last_pump_activation_time:
                    time_since_last_activation = datetime.now() - self.last_pump_activation_time
                    if time_since_last_activation < self.pump_cooldown:
                        logging.warning(f"Pump activation blocked due to cooldown. Time remaining: {self.pump_cooldown - time_since_last_activation}")
                        sanitized_action['pump_status'] = 0 # Override to off
                    else:
                        # Cooldown has passed, allow activation and update timestamp
                        self.last_pump_activation_time = datetime.now()
                else:
                    # First time the pump is activated
                    self.last_pump_activation_time = datetime.now()

        return sanitized_action

    def _get_safe_default(self) -> dict:
        """Returns a default safe action."""
        return {
            "gate_opening": 0.0,
            "pump_status": 0
        }
