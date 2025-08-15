import yaml
import importlib
from typing import Dict, Any
import pandas as pd


class MotherMachine:
    """
    The MotherMachine is responsible for generating agent society configurations
    from high-level templates and parameters, and for running workflows.
    """

    def __init__(self, template_path=None):
        """
        Initializes the MotherMachine.

        :param template_path: Path to a directory containing configuration templates.
                              (Not used in this prototype version).
        """
        self.templates = {
            "single_tank_pid": self._get_single_tank_pid_template(),
            "identified_body_agent": self._get_identified_body_agent_template()
        }
        self.workflows = {}

    def _get_single_tank_pid_template(self):
        """
        Returns a hardcoded template for a single tank PID control scenario.
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

    def _get_identified_body_agent_template(self):
        """
        Returns a template for a BodyAgent whose parameters are identified from data.
        """
        return {
            "id": "{{agent_id}}",
            "class": "chs_sdk.agents.body_agents.IdentifiedParameterAgent",
            "params": {
                "model_type": "{{model_type}}",
                "identified_parameters": "{{identified_parameters}}",
                "initial_state": "{{initial_state}}"
            }
        }

    def generate_config(self, template_name: str, params: dict) -> dict:
        """
        Generates a full configuration dictionary from a template and parameters.
        """
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found.")

        template_str = yaml.dump(self.templates[template_name])

        for key, value in params.items():
            placeholder = f"{{{{{key}}}}}"
            if isinstance(value, (dict, list)):
                value_str = yaml.dump(value, default_flow_style=True).strip()
                template_str = template_str.replace(f"'{placeholder}'", value_str)
            else:
                template_str = template_str.replace(placeholder, str(value))

        final_config = yaml.safe_load(template_str)
        return final_config

    def run_workflow(self, workflow_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dynamically loads and runs a specified workflow.
        """
        if workflow_name not in self.workflows:
            try:
                module = importlib.import_module(f"chs_sdk.workflows.{workflow_name}")
                # Expecting a class named "SystemIDWorkflow" in a file "system_id_workflow.py"
                # Correctly handle "ID" as a special case in the class name.
                class_name = ''.join(word.upper() if word.lower() == 'id' else word.title() for word in workflow_name.split('_'))
                workflow_class = getattr(module, class_name)
                self.workflows[workflow_name] = workflow_class()
            except (ImportError, AttributeError) as e:
                raise ImportError(f"Could not load workflow '{workflow_name}': {e}")

        workflow_instance = self.workflows[workflow_name]
        return workflow_instance.run(context)

    def design_body_agent_from_data(self, agent_id: str, data: pd.DataFrame, model_type: str,
                                    dt: float, initial_guess: list, bounds: list) -> Dict[str, Any]:
        """
        Designs a BodyAgent configuration by identifying its model from data.
        """
        # 1. Prepare context for the System ID workflow
        context = {
            "data": data,
            "model_type": model_type,
            "dt": dt,
            "initial_guess": initial_guess,
            "bounds": bounds
        }

        # 2. Run the workflow to get model parameters
        result = self.run_workflow("system_id_workflow", context)

        if result.get("status") != "success":
            raise RuntimeError(f"SystemIDWorkflow failed: {result.get('error', 'Unknown error')}")

        # 3. Convert numpy types to standard Python types for YAML compatibility
        identified_params = result["identified_parameters"]
        cleaned_params = {k: float(v) for k, v in identified_params.items()}

        # 4. Prepare parameters to fill the agent template
        config_params = {
            "agent_id": agent_id,
            "model_type": model_type,
            "identified_parameters": cleaned_params,
            "initial_state": {"outflow": float(data['outflow'].iloc[0])}  # Use first value as initial state
        }

        # 5. Generate the final agent configuration
        return self.generate_config("identified_body_agent", config_params)

    def design_optimal_controller(self, system_model: Dict[str, Any], optimization_objective: str,
                                  parameter_bounds: list, initial_guess: list) -> Dict[str, Any]:
        """
        Designs an optimal PID controller by running the control tuning workflow.

        Args:
            system_model: The system the controller will be designed for.
            optimization_objective: The metric to optimize (e.g., 'ISE').
            parameter_bounds: Bounds for each parameter.
            initial_guess: Initial guess for the parameters [Kp, Ki, Kd].

        Returns:
            A dictionary containing the optimal PID parameters.
        """
        # 1. Prepare context for the Control Tuning workflow
        context = {
            "system_model": system_model,
            "optimization_objective": optimization_objective,
            "parameter_bounds": parameter_bounds,
            "initial_guess": initial_guess,
        }

        # 2. Run the workflow to get optimal controller parameters
        result = self.run_workflow("control_tuning_workflow", context)

        # 3. Clean up the result for direct use
        # The optimizer returns numpy types, which we convert to standard floats.
        optimal_params = {k: float(v) for k, v in result["optimal_params"].items()}

        return optimal_params


# Example usage (can be run for testing)
if __name__ == '__main__':
    mother_machine = MotherMachine()

    # --- Example 1: Original functionality ---
    print("--- Running Original Template Filler ---")
    business_params = {
        "duration": 100, "tank_id": "main_tank_123", "tank_area": 150.0,
        "initial_level": 4.5, "set_point": 10.0, "kp": 0.55, "ki": 0.12, "kd": 0.02,
        "inflow_pattern": [15] * 50 + [0] * 50
    }
    try:
        config_dict = mother_machine.generate_config("single_tank_pid", business_params)
        print("Generated PID Controller Configuration:")
        print(yaml.dump(config_dict, sort_keys=False))
    except ValueError as e:
        print(e)

    # --- Example 2: New System ID Workflow functionality ---
    print("\n--- Running New System ID Workflow ---")
    # Create sample data for a Muskingum model
    # In a real scenario, this data would come from sensors.
    sample_data = {
        'time': range(100),
        'inflow': [10, 11, 12, 13, 14, 15, 14, 13, 12, 11] * 10,
        # A plausible outflow that lags and attenuates the inflow
        'outflow': [9, 9.5, 10.5, 11.5, 12.5, 13.5, 13, 12, 11, 10] * 10
    }
    sample_df = pd.DataFrame(sample_data)

    try:
        agent_config = mother_machine.design_body_agent_from_data(
            agent_id="river_reach_1",
            data=sample_df,
            model_type="Muskingum",
            dt=1.0,
            initial_guess=[10.0, 0.2], # Initial guess for K and X
            bounds=[(0, 100), (0, 0.5)] # Bounds for K and X
        )
        print("\nGenerated Body Agent Configuration from Data:")
        print(yaml.dump(agent_config, sort_keys=False))

    except (ImportError, RuntimeError, ValueError) as e:
        print(f"Error during agent design from data: {e}")
