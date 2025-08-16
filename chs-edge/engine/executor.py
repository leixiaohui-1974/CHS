import logging
import threading
from enum import Enum, auto
from engine.loader import load_agent
from engine.fallback_agent import FallbackAgent
from engine.safety_wrapper import SafetyWrapper
from drivers.hardware_interface import MockHardware

class ExecutorState(Enum):
    """Defines the operational states of the Executor."""
    RUNNING = auto()
    FALLBACK = auto()
    ERROR = auto()

class Executor:
    def __init__(self, hardware_interface, model_path: str):
        """
        Initializes the Executor.

        Args:
            hardware_interface: An instance of a hardware interface.
            model_path: The initial path to the agent model file.
        """
        self.hardware = hardware_interface
        self.model_path = model_path
        self.agent = None
        self.fallback_agent = FallbackAgent()
        self.safety_wrapper = SafetyWrapper()
        self._lock = threading.Lock() # To safely reload the agent or change state
        self.state = ExecutorState.RUNNING

        self.reload_agent(model_path)
        # If agent loading fails, we should start in fallback mode.
        if not self.agent:
            self.state = ExecutorState.FALLBACK
            logging.warning("No primary agent loaded. Starting in FALLBACK mode.")


    def enter_fallback_mode(self):
        """Switches the executor to FALLBACK state."""
        with self._lock:
            if self.state != ExecutorState.FALLBACK:
                self.state = ExecutorState.FALLBACK
                logging.warning("Entering FALLBACK mode due to external trigger (e.g., network loss).")

    def exit_fallback_mode(self):
        """Switches the executor to RUNNING state if a primary agent is available."""
        with self._lock:
            if self.state == ExecutorState.FALLBACK:
                if self.agent:
                    self.state = ExecutorState.RUNNING
                    logging.info("Exiting FALLBACK mode. Resuming normal operation with primary agent.")
                else:
                    logging.warning("Cannot exit FALLBACK mode: no primary agent is loaded.")

    def reload_agent(self, model_path: str):
        """
        Loads or reloads the agent from the given path.
        This method is thread-safe.
        """
        logging.info(f"Attempting to load agent from: {model_path}")
        new_agent = load_agent(model_path)
        if new_agent:
            with self._lock:
                self.agent = new_agent
                self.model_path = model_path
                logging.info(f"Successfully loaded agent: {self.agent.agent_id}")
            return True
        else:
            logging.error(f"Failed to load agent from: {model_path}. Keeping the old agent if available.")
            return False

    def run_step(self):
        """
        Runs a single step of the perceive-decide-act loop.
        The agent used depends on the current ExecutorState.
        """
        # 1. Perceive: Read sensor data from the hardware
        observation = self.hardware.read_sensors()
        if not observation:
            logging.warning("Received no observation from hardware, skipping step.")
            return
        logging.info(f"[EXECUTOR] Got observation: {observation}")

        # 2. Decide: Get an action from the appropriate agent based on the state
        action = None
        with self._lock:
            current_state = self.state
            if current_state == ExecutorState.RUNNING and self.agent:
                action = self.agent.execute(observation)
                logging.info(f"[EXECUTOR] Primary agent proposed action: {action}")
            elif current_state == ExecutorState.FALLBACK:
                action = self.fallback_agent.execute(observation)
                logging.info(f"[EXECUTOR] Fallback agent proposed action: {action}")
            else:
                logging.error(f"Executor in unhandled state '{current_state}' or no agent available. Skipping action.")
                return

        # 3. Act: Pass the action through the safety wrapper and then to the hardware
        if action:
            sanitized_action = self.safety_wrapper.validate_and_sanitize(action)
            self.hardware.write_actuators(sanitized_action)

    def update_agent_parameters(self, params: dict):
        """
        Updates parameters of the currently running agent.
        This method is thread-safe.
        """
        if not self.agent:
            logging.warning("Cannot update parameters, no agent is loaded.")
            return

        logging.info(f"Attempting to update agent parameters with: {params}")
        with self._lock:
            try:
                # Assumes the agent has a method 'update_parameters'
                if hasattr(self.agent, 'update_parameters') and callable(self.agent.update_parameters):
                    self.agent.update_parameters(params)
                    logging.info("Agent parameters updated successfully.")
                else:
                    logging.warning(f"Agent of type {type(self.agent).__name__} does not have an 'update_parameters' method.")
            except Exception as e:
                logging.error(f"Failed to update agent parameters: {e}")
