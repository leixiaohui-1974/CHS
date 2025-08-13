from water_system_simulator.modeling.base_model import BaseModel

class RuleBasedOperationalController(BaseModel):
    def __init__(self, rules: list, default_actions: dict, **kwargs):
        """
        Initializes the RuleBasedOperationalController.

        Args:
            rules (list): A list of rules, where each rule is a dictionary
                          with 'if' and 'then' keys.
            default_actions (dict): A dictionary of default actions to take
                                    when no rules are met.
        """
        super().__init__(**kwargs)
        self.rules = rules
        self.default_actions = default_actions
        self.current_actions = default_actions.copy()

    def step(self, system_state: dict, dt: float):
        """
        Evaluates the rules against the current system state and updates
        the control actions accordingly.

        Args:
            system_state (dict): The current state of the entire system.
            dt (float): The time step for the simulation.
        """
        self.current_actions = self.default_actions.copy()

        for rule in self.rules:
            conditions_met = True
            for condition in rule['if']:
                try:
                    comp_id, _, var_path_str = condition['variable'].partition('.')
                    if comp_id not in system_state:
                        raise KeyError(f"Component '{comp_id}' not found.")

                    component_obj = system_state[comp_id]
                    path_keys = var_path_str.split('.')

                    # The user-defined rule format "component.state.variable" implies
                    # that 'state' is a special keyword to access the component's state dict.
                    if path_keys[0] == 'state':
                        if not hasattr(component_obj, 'get_state'):
                            raise AttributeError(f"Component '{comp_id}' has no get_state method.")

                        # Get the state dictionary, e.g., {'level': 5.0}
                        current_value = component_obj.get_state()

                        # Access the variable within the state dictionary
                        for key in path_keys[1:]: # e.g., ['level']
                            current_value = current_value[key]
                        actual_value = current_value
                    else:
                        # Fallback for accessing direct attributes if needed in the future,
                        # though the primary design uses the 'state' keyword.
                        current_value = component_obj
                        for key in path_keys:
                            current_value = getattr(current_value, key)
                        actual_value = current_value

                except (KeyError, AttributeError, TypeError) as e:
                    # If any part of the path fails, the condition is not met.
                    conditions_met = False
                    break

                operator = condition['operator']
                target_value = condition['value']

                if not self._evaluate_condition(actual_value, operator, target_value):
                    conditions_met = False
                    break

            if conditions_met:
                self.current_actions = rule['then']
                break

    def _evaluate_condition(self, actual, op, target):
        """
        Evaluates a single condition.
        """
        if op == '>':
            return actual > target
        if op == '<':
            return actual < target
        if op == '==':
            return actual == target
        if op == '>=':
            return actual >= target
        if op == '<=':
            return actual <= target
        if op == '!=':
            return actual != target
        return False

    def get_state(self) -> dict:
        """
        Returns the current control actions.
        """
        return self.current_actions
