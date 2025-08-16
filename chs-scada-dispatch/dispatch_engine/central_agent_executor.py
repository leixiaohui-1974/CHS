import logging
import time
import threading
import uuid
from typing import Optional, Dict, Any

# Mock Agent for simulation purposes
class MockManagementAgent:
    """
    A mock central agent that decides to adjust pump speed if pressure is too high,
    and requests human intervention for moderately high pressure.
    This simulates a real agent from the 'chs-sdk'.
    """
    def execute(self, observation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Executes a decision based on the system-wide observation.
        """
        for device_id, status in observation.items():
            pressure = status.get("values", {}).get("pressure_psi")
            if not pressure:
                continue

            # Condition 1: High pressure -> Automatic command
            if pressure > 120:
                logging.info(f"[Agent] High pressure at {device_id} ({pressure} psi). Proposing automatic command.")
                return {
                    "action_type": "command",
                    "target_device_id": device_id,
                    "command": {"set_pump_speed": 0.85},
                    "description": f"Automatically reduce pump speed at {device_id} due to high pressure ({pressure} psi)."
                }

            # Condition 2: Moderately high pressure -> Request Human-in-the-Loop
            if 110 <= pressure <= 120:
                logging.info(f"[Agent] Moderate pressure at {device_id} ({pressure} psi). Proposing Human-in-the-Loop.")
                return {
                    "action_type": "human_in_the_loop",
                    "request_id": str(uuid.uuid4()),
                    "target_device_id": device_id,
                    "proposed_command": {"set_pump_speed": 0.9},
                    "description": f"Pressure at {device_id} is moderately high ({pressure} psi). Recommend reducing pump speed to 90%. Please confirm."
                }

        return None # No action needed

class CentralExecutor:
    """
    Loads and executes a central-level intelligent agent for system-wide control,
    including handling Human-in-the-Loop (HITL) decision flows.
    """
    def __init__(self, timeseries_db, mqtt_service, websocket_service=None):
        self.timeseries_db = timeseries_db
        self.mqtt_service = mqtt_service
        self.websocket_service = websocket_service
        self.agent = None
        self.is_running = False
        self.thread = None
        self.decision_interval_sec = 15

        # For handling HITL requests
        self._human_decision_events: Dict[str, threading.Event] = {}
        self._human_decisions: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def load_agent(self, agent_path: str):
        """
        Loads and initializes a central agent from a (simulated) deployment package.
        """
        logging.info(f"Simulating loading agent from: {agent_path}")
        self.agent = MockManagementAgent()
        logging.info("MockManagementAgent loaded successfully.")

    def _handle_hitl_request(self, action: Dict[str, Any]):
        """Handles the logic for a Human-in-the-Loop request."""
        request_id = action.get("request_id")
        if not request_id:
            logging.error("HITL action is missing a 'request_id'.")
            return

        # Prepare for receiving a response
        event = threading.Event()
        with self._lock:
            self._human_decision_events[request_id] = event
            self._human_decisions.pop(request_id, None) # Clear any old decision

        # Send request to HMI via WebSocket
        if self.websocket_service:
            logging.info(f"Requesting human decision for request_id: {request_id}")
            self.websocket_service.emit('decision_request', action)
        else:
            logging.error("WebSocket service is not available for HITL request.")
            return

        # Wait for the human response
        timeout_sec = 60.0
        logging.info(f"Waiting for human response for {timeout_sec} seconds...")
        event_was_set = event.wait(timeout=timeout_sec)

        with self._lock:
            decision = self._human_decisions.pop(request_id, None)
            self._human_decision_events.pop(request_id, None)

        if event_was_set and decision:
            logging.info(f"Human responded for request {request_id}: {decision}")
            if decision.get("approved"):
                # Human approved, publish the command
                device_id = action.get("target_device_id")
                command = action.get("proposed_command")
                self.mqtt_service.publish_command(device_id, command)
            else:
                logging.info(f"Human rejected the proposal for request {request_id}.")
        else:
            logging.warning(f"HITL request {request_id} timed out. No action taken.")

    def submit_human_decision(self, request_id: str, decision: Dict[str, Any]):
        """Callback for the WebSocket service to submit a human's decision."""
        with self._lock:
            event = self._human_decision_events.get(request_id)
            if event:
                self._human_decisions[request_id] = decision
                event.set() # Signal that the decision has been made
                logging.info(f"Human decision for {request_id} received and event set.")
            else:
                logging.warning(f"Received decision for an unknown or expired request_id: {request_id}")


    def run_decision_cycle(self):
        """The main loop for the dispatch engine."""
        while self.is_running:
            logging.info("Starting new decision cycle...")
            observation = self.timeseries_db.get_latest_statuses()

            if not observation:
                logging.warning("Observation is empty. Skipping decision cycle.")
                time.sleep(self.decision_interval_sec)
                continue

            if not self.agent:
                logging.error("No agent loaded. Cannot execute decision cycle.")
                time.sleep(self.decision_interval_sec)
                continue

            action = self.agent.execute(observation)

            if action:
                logging.info(f"Agent proposed an action: {action}")
                action_type = action.get("action_type")

                if action_type == "command":
                    device_id = action.get("target_device_id")
                    command = action.get("command")
                    if device_id and command:
                        self.mqtt_service.publish_command(device_id, command)
                elif action_type == "human_in_the_loop":
                    # Run HITL in a separate thread to not block the main decision cycle
                    hitl_thread = threading.Thread(target=self._handle_hitl_request, args=(action,))
                    hitl_thread.start()
                else:
                    logging.warning(f"Unknown action type: {action_type}")
            else:
                logging.info("No action was proposed by the agent in this cycle.")

            time.sleep(self.decision_interval_sec)

    def start(self):
        """Starts the dispatch engine's decision cycle in a background thread."""
        if self.is_running:
            logging.warning("Dispatch engine is already running.")
            return
        self.load_agent("chs-sdk/dist/ManagementAgent.agent")
        self.is_running = True
        self.thread = threading.Thread(target=self.run_decision_cycle, daemon=True)
        self.thread.start()
        logging.info("Central Dispatch Engine started.")

    def stop(self):
        """Stops the dispatch engine."""
        if self.is_running:
            self.is_running = False
            if self.thread:
                self.thread.join()
            logging.info("Central Dispatch Engine stopped.")
