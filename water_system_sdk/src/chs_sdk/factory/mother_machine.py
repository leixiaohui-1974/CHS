import yaml

class MotherMachine:
    """
    The MotherMachine is responsible for generating agent society configurations
    from high-level templates and parameters.
    """

    def __init__(self, template_path=None):
        """
        Initializes the MotherMachine.

        :param template_path: Path to a directory containing configuration templates.
                              (Not used in this prototype version).
        """
        self.templates = {
            "single_tank_pid": self._get_single_tank_pid_template()
        }

    def _get_single_tank_pid_template(self):
        """
        Returns a hardcoded template for a single tank PID control scenario.
        In a real implementation, this would load from a YAML file.
        """
        return {
            "simulation_settings": {
                "duration": "{{duration}}",
                "time_step": 1.0
            },
            "agent_society": [
                {
                    "id": "inflow_agent_1",
                    "class": "chs_sdk.agents.disturbance_agents.InflowAgent",
                    "params": {
                        "topic": "tank/{{tank_id}}/inflow",
                        "rainfall_pattern": "{{inflow_pattern}}"
                    }
                },
                {
                    "id": "{{tank_id}}",
                    "class": "chs_sdk.agents.body_agents.TankAgent",
                    "params": {
                        "area": "{{tank_area}}",
                        "initial_level": "{{initial_level}}",
                        "max_level": 20.0
                    }
                },
                {
                    "id": "pid_agent_1",
                    "class": "chs_sdk.agents.control_agents.PIDAgent",
                    "params": {
                        "Kp": "{{kp}}",
                        "Ki": "{{ki}}",
                        "Kd": "{{kd}}",
                        "set_point": "{{set_point}}",
                        "input_topic": "tank/{{tank_id}}/state",
                        "output_topic": "tank/{{tank_id}}/release_outflow",
                        "output_min": 0,
                        "output_max": 20
                    }
                }
            ]
        }

    def generate_config(self, template_name: str, params: dict) -> dict:
        """
        Generates a full configuration dictionary from a template and parameters.

        :param template_name: The name of the template to use (e.g., "single_tank_pid").
        :param params: A dictionary of parameters to fill into the template.
        :return: A complete configuration dictionary.
        :raises ValueError: If the template name is not found.
        """
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found.")

        # Convert the template dictionary to a string to do simple text replacement
        template_str = yaml.dump(self.templates[template_name])

        # Replace placeholders (e.g., "{{param_name}}") with actual values
        for key, value in params.items():
            placeholder = f"{{{{{key}}}}}"
            # Special handling for lists/arrays so they are dumped correctly in YAML
            if isinstance(value, list):
                # Quick YAML dump of the list to format it correctly
                value_str = yaml.dump(value, default_flow_style=True).strip()
                template_str = template_str.replace(f"'{placeholder}'", value_str)
            else:
                template_str = template_str.replace(placeholder, str(value))

        # Convert the string back to a dictionary
        final_config = yaml.safe_load(template_str)

        return final_config

# Example usage (can be run for testing)
if __name__ == '__main__':
    mother_machine = MotherMachine()

    # Define high-level business requirements
    business_params = {
        "duration": 100,
        "tank_id": "main_tank_123",
        "tank_area": 150.0,
        "initial_level": 4.5,
        "set_point": 10.0,
        "kp": 0.55,
        "ki": 0.12,
        "kd": 0.02,
        "inflow_pattern": [15] * 50 + [0] * 50 # Example pattern
    }

    # Generate the configuration
    try:
        config_dict = mother_machine.generate_config("single_tank_pid", business_params)

        # Print the generated YAML configuration
        print("Generated Configuration:")
        print(yaml.dump(config_dict, sort_keys=False))

    except ValueError as e:
        print(e)
