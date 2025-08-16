import logging
import threading
from engine.loader import load_agent
from drivers.hardware_interface import MockHardware

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
        self._lock = threading.Lock() # To safely reload the agent
        self.reload_agent(model_path)

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
        """
        if not self.agent:
            logging.warning("Executor has no agent loaded, skipping run step.")
            return

        # 1. Perceive: Read sensor data from the hardware
        observation = self.hardware.read_sensors()
        if not observation:
            logging.warning("Received no observation from hardware, skipping step.")
            return
        logging.info(f"[EXECUTOR] Got observation: {observation}")

        # 2. Decide: Get an action from the agent based on the observation
        with self._lock:
            action = self.agent.execute(observation)
        logging.info(f"[EXECUTOR] Agent proposed action: {action}")

        # 3. Act: Send the action to the hardware to be executed
        self.hardware.write_actuators(action)

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
