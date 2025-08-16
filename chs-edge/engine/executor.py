import logging
from engine.loader import load_agent
from drivers.hardware_interface import MockHardware


class Executor:
    def __init__(self, hardware: MockHardware, model_path: str = 'path/to/model.agent'):
        """
        Initializes the Executor.

        Args:
            hardware: An instance of a hardware interface.
            model_path: The path to the agent model file.
        """
        self.hardware = hardware
        self.agent = load_agent(model_path)
        logging.info(f"Agent {self.agent.agent_id} loaded.")

    def run_step(self):
        """
        Runs a single step of the perceive-decide-act loop.
        """
        # 1. Perceive: Read sensor data from the hardware
        observation = self.hardware.read_sensors()
        logging.info(f"[EXECUTOR] Got observation: {observation}")

        # 2. Decide: Get an action from the agent based on the observation
        action = self.agent.execute(observation)
        logging.info(f"[EXECUTOR] Agent proposed action: {action}")

        # 3. Act: Send the action to the hardware to be executed
        self.hardware.write_actuators(action)
