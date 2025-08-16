import os
import time
import logging
from dotenv import load_dotenv
from drivers.hardware_interface import get_hardware_interface
from engine.executor import Executor
from services.mqtt_service import MqttService

def setup_logging():
    """Configures the logging format and level."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def main():
    """
    The main entry point for the CHS-Edge application.
    """
    setup_logging()

    # Load configuration from .env file
    load_dotenv(dotenv_path='config.env')
    config = dict(os.environ)
    logging.info("Configuration loaded.")

    # --- Initialization ---
    # 1. Initialize Hardware Interface
    hardware = get_hardware_interface(config)

    # 2. Initialize Agent Executor
    initial_model = config.get('INITIAL_MODEL_PATH', 'model.agent')
    # A sample agent needs to be created for the application to run.
    # This part would typically be handled by a factory or deployment process.
    if not os.path.exists(initial_model):
        logging.warning(f"Initial model '{initial_model}' not found. A placeholder will be needed.")
        # In a real scenario, you might want to exit or wait for a model to be pushed.
        # For this example, we can't proceed without a model, so we will exit.
        print("Please create a sample 'sample_agent.agent' file and run again.")
        print("This file should be a zip containing 'config.json' and a pickled agent model.")
        return

    executor = Executor(hardware_interface=hardware, model_path=initial_model)

    # 3. Initialize MQTT Service
    mqtt_service = MqttService(executor=executor, config=config)
    mqtt_service.run()

    # --- Main Loop ---
    logging.info("Starting main application loop...")
    try:
        while True:
            executor.run_step()
            time.sleep(1) # Control loop frequency
    except KeyboardInterrupt:
        logging.info("Shutdown signal received.")
    finally:
        logging.info("Stopping services...")
        mqtt_service.stop()
        logging.info("Application shut down gracefully.")

if __name__ == "__main__":
    main()
