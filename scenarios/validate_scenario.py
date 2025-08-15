import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'water_system_sdk', 'src')))

import yaml
import importlib
import inspect
from typing import Dict, Any, List

class ScenarioValidator:
    """
    A class to validate a CHS-SDK scenario configuration file.
    """
    def __init__(self, config_path: str):
        """
        Initializes the validator with the path to the config file.

        :param config_path: Path to the scenario's config.yaml file.
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def _load_config(self) -> Dict[str, Any]:
        """
        Loads the YAML configuration file.
        """
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.errors.append(f"Configuration file not found at: {self.config_path}")
            return {}
        except yaml.YAMLError as e:
            self.errors.append(f"Error parsing YAML file: {e}")
            return {}

    def validate(self) -> bool:
        """
        Runs all validation checks.

        :return: True if the configuration is valid (no errors), False otherwise.
        """
        if not self.config:
            return False

        self.check_class_path_existence()
        self.check_dangling_subscriptions()
        self.check_required_parameters()

        return not self.errors

    def check_class_path_existence(self):
        """
        Checks if the class path for each agent points to a real, importable class.
        """
        agents = self.config.get('agent_society', [])
        for i, agent_config in enumerate(agents):
            class_path = agent_config.get('class')
            if not class_path:
                self.errors.append(f"Agent #{i+1} (id: {agent_config.get('id', 'N/A')}) is missing the 'class' key.")
                continue

            try:
                module_name, class_name = class_path.rsplit('.', 1)
                module = importlib.import_module(module_name)
                getattr(module, class_name)
            except ImportError:
                self.errors.append(f"Agent '{agent_config.get('id', 'N/A')}': Module '{module_name}' not found for class path '{class_path}'.")
            except AttributeError:
                self.errors.append(f"Agent '{agent_config.get('id', 'N/A')}': Class '{class_name}' not found in module '{module_name}'.")
            except ValueError:
                self.errors.append(f"Agent '{agent_config.get('id', 'N/A')}': Invalid class path format '{class_path}'.")

    def check_dangling_subscriptions(self):
        """
        Checks for agents that subscribe to topics that are never published to.
        """
        agents = self.config.get('agent_society', [])
        if not agents:
            return

        published_topics = set()

        # This is a simplified check. A more robust implementation would need to
        # parse the agent's documentation or code to know what it publishes.
        # For now, we rely on an explicit 'publishes_to' key.
        for agent_config in agents:
            params = agent_config.get('params', {})
            # Handle various ways topics can be published
            for key in ['publishes_to', 'topic', 'output_topic', 'state_topic']:
                if key in params:
                    topic = params[key]
                    if isinstance(topic, str):
                        published_topics.add(topic)
                    elif isinstance(topic, list):
                        published_topics.update(topic)

        # Also need to consider conventionally named topics
        for agent_config in agents:
            agent_id = agent_config.get('id')
            if not agent_id:
                continue

            # Add conventional topics based on agent type
            # This is not exhaustive and is just an example
            class_path = agent_config.get('class', '')
            if 'TankAgent' in class_path:
                published_topics.add(f"tank/{agent_id}/state")
            if 'ValveAgent' in class_path:
                published_topics.add(f"state/valve/{agent_id}")


        all_subscriptions = set()
        for agent_config in agents:
            params = agent_config.get('params', {})
            # Handle various ways topics can be subscribed to
            for key in ['subscribes_to', 'input_topic', 'state_topic', 'upstream_topic', 'downstream_topic', 'opening_topic', 'inlet_pressure_topic', 'outlet_pressure_topic', 'num_pumps_on_topic', 'vane_opening_topic']:
                 if key in params:
                    topic = params[key]
                    if isinstance(topic, str):
                        all_subscriptions.add(topic)
                    elif isinstance(topic, list):
                        all_subscriptions.update(topic)

        dangling_topics = all_subscriptions - published_topics
        for topic in dangling_topics:
            self.warnings.append(f"Dangling subscription: Topic '{topic}' is subscribed to but never published to by any agent in this config.")

    def check_required_parameters(self):
        """
        Checks if all required parameters for each agent are present in the config.
        Uses introspection to determine required parameters from the class __init__ signature.
        """
        agents = self.config.get('agent_society', [])
        for i, agent_config in enumerate(agents):
            class_path = agent_config.get('class')
            if not class_path:
                continue # This error is already handled by check_class_path_existence

            try:
                module_name, class_name = class_path.rsplit('.', 1)
                module = importlib.import_module(module_name)
                agent_class = getattr(module, class_name)

                sig = inspect.signature(agent_class.__init__)
                required_params = [
                    p.name for p in sig.parameters.values()
                    if p.default is inspect.Parameter.empty and p.name not in ['self', 'agent_id', 'kernel', 'kwargs']
                ]

                provided_params = agent_config.get('params', {})
                if not isinstance(provided_params, dict):
                    self.errors.append(f"Agent '{agent_config.get('id', 'N/A')}': 'params' section is not a dictionary.")
                    continue

                missing_params = set(required_params) - set(provided_params.keys())

                if missing_params:
                    self.errors.append(f"Agent '{agent_config.get('id', 'N/A')}' ({class_name}): Missing required parameters: {', '.join(sorted(list(missing_params)))}")

            except (ImportError, AttributeError, ValueError):
                # These errors are handled by check_class_path_existence, so we can ignore them here.
                continue

    def print_results(self):
        """
        Prints the validation results to the console.
        """
        print(f"--- Validation Results for {self.config_path} ---")
        if not self.errors and not self.warnings:
            print("✅ Configuration is valid.")
        else:
            if self.warnings:
                print("\nWarnings:")
                for warning in self.warnings:
                    print(f"  - ⚠️ {warning}")
            if self.errors:
                print("\nErrors:")
                for error in self.errors:
                    print(f"  - ❌ {error}")
        print("-------------------------------------------------")


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python validate_scenario.py <path_to_config.yaml>")
        sys.exit(1)

    validator = ScenarioValidator(sys.argv[1])
    is_valid = validator.validate()
    validator.print_results()

    # Exit with a non-zero status code if errors are found
    if not is_valid:
        sys.exit(1)
