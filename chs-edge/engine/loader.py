import zipfile
import json
import pickle
import os
import tempfile
import logging
from chs_sdk.agents.control import PIDControlAgent

def load_agent_from_zip(model_path: str):
    """
    Loads a CHS Agent from a .agent (zip) file.

    The .agent file is expected to contain:
    - a 'config.json' file with metadata.
    - the agent model file (e.g., 'model.pkl').

    Args:
        model_path: The file path to the .agent zip archive.

    Returns:
        An instantiated agent object, or None if loading fails.
    """
    if not os.path.exists(model_path):
        logging.error(f"Agent file not found at: {model_path}")
        return None

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            with zipfile.ZipFile(model_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                logging.info(f"Extracted agent file to temporary directory: {temp_dir}")
        except zipfile.BadZipFile:
            logging.error(f"Error: The file at {model_path} is not a valid zip archive.")
            return None

        config_path = os.path.join(temp_dir, 'config.json')
        if not os.path.exists(config_path):
            logging.error(f"Agent config.json not found in {model_path}")
            return None

        with open(config_path, 'r') as f:
            config = json.load(f)

        model_file = config.get('model_file')
        if not model_file:
            logging.error("Config does not specify a 'model_file'")
            return None

        model_file_path = os.path.join(temp_dir, model_file)
        if not os.path.exists(model_file_path):
            logging.error(f"Model file '{model_file}' not found in the agent archive.")
            return None

        agent_class_name = config.get('agent_class')

        # This is a simplified dynamic loading. A real implementation might be more robust.
        # For now, we assume it's a PIDControlAgent that can be loaded with pickle.
        if agent_class_name == 'PIDControlAgent':
            try:
                with open(model_file_path, 'rb') as f:
                    agent_instance = pickle.load(f)
                logging.info(f"Successfully loaded agent '{agent_instance.agent_id}' from {model_path}")
                return agent_instance
            except Exception as e:
                logging.error(f"Failed to load agent from pickle file: {e}")
                return None
        else:
            logging.error(f"Unsupported agent class: {agent_class_name}")
            return None

# Alias for backward compatibility if needed, or for clarity.
load_agent = load_agent_from_zip
