import logging
import time
import threading
from typing import Optional, Dict, Any

# Mock Agent for simulation purposes
class MockManagementAgent:
    """
    A mock central agent that decides to adjust pump speed if pressure is too high.
    This simulates a real agent from the 'chs-sdk'.
    """
    def execute(self, observation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Executes a decision based on the system-wide observation.
        """
        for device_id, status in observation.items():
            # Example logic: If a pump station's pressure is above 120, reduce pump speed.
            pressure = status.get("values", {}).get("pressure_psi")
            if pressure and pressure > 120:
                logging.info(f"[Agent] High pressure detected at {device_id} ({pressure} psi). Deciding to reduce pump speed.")
                return {
                    "action_type": "command",
                    "target_device_id": device_id,
                    "command": {"set_pump_speed": 0.85}
                }
        return None # No action needed

class CentralExecutor:
    """
    Loads and executes a central-level intelligent agent for system-wide control.
    """
    def __init__(self, timeseries_db, mqtt_service, websocket_service=None):
        self.timeseries_db = timeseries_db
        self.mqtt_service = mqtt_service
        self.websocket_service = websocket_service # For future HITL integration
        self.agent = None
        self.is_running = False
        self.thread = None
        self.decision_interval_sec = 15  # Run decision cycle every 15 seconds

    def load_agent(self, agent_path: str):
        """
        Loads and initializes a central agent from a (simulated) deployment package.
        """
        # In a real scenario, this would involve parsing the .agent file.
        # For Phase 2, we'll just instantiate our mock agent.
        logging.info(f"Simulating loading agent from: {agent_path}")
        self.agent = MockManagementAgent()
        logging.info("MockManagementAgent loaded successfully.")

    def run_decision_cycle(self):
        """
        The main loop for the dispatch engine.
        """
        while self.is_running:
            logging.info("Starting new decision cycle...")

            # 1. Get system state (observation)
            observation = self.timeseries_db.get_latest_statuses()
            if not observation:
                logging.warning("Observation is empty. Skipping decision cycle.")
                time.sleep(self.decision_interval_sec)
                continue

            # 2. Execute agent logic
            if not self.agent:
                logging.error("No agent loaded. Cannot execute decision cycle.")
                time.sleep(self.decision_interval_sec)
                continue

            action = self.agent.execute(observation)

            # 3. Process agent's action
            if action:
                logging.info(f"Agent proposed an action: {action}")
                if action.get("action_type") == "command":
                    device_id = action.get("target_device_id")
                    command = action.get("command")
                    if device_id and command:
                        self.mqtt_service.publish_command(device_id, command)
                # Future: Could have an 'human_in_the_loop' action_type
                # that would use self.websocket_service
            else:
                logging.info("No action was proposed by the agent in this cycle.")

            # Wait for the next cycle
            time.sleep(self.decision_interval_sec)

    def start(self):
        """
        Starts the dispatch engine's decision cycle in a background thread.
        """
        if self.is_running:
            logging.warning("Dispatch engine is already running.")
            return

        # For now, we simulate loading a default agent on start
        self.load_agent("chs-sdk/dist/ManagementAgent.agent")

        self.is_running = True
        self.thread = threading.Thread(target=self.run_decision_cycle, daemon=True)
        self.thread.start()
        logging.info("Central Dispatch Engine started.")

    def stop(self):
        """
        Stops the dispatch engine.
        """
        if self.is_running:
            self.is_running = False
            if self.thread:
                self.thread.join() # Wait for the thread to finish
            logging.info("Central Dispatch Engine stopped.")
