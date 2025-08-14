import unittest
from water_system_simulator.control.rule_based_controller import RuleBasedOperationalController

# A mock component to simulate the objects in the system_state dictionary
class MockStatefulComponent:
    def __init__(self, state):
        self._state = state
    def get_state(self):
        return self._state

class TestRuleBasedOperationalController(unittest.TestCase):

    def test_simple_rule_triggers(self):
        rules = [
            {
                "if": [{"variable": "reservoir.state.level", "operator": ">", "value": 10}],
                "then": {"command": 1}
            }
        ]
        default_actions = {"command": 0}
        controller = RuleBasedOperationalController(rules=rules, default_actions=default_actions)

        # Mock system state where the condition is met
        system_state = {"reservoir": MockStatefulComponent({"level": 11})}
        controller.step(system_state, dt=1)
        self.assertEqual(controller.get_state(), {"command": 1})

        # Mock system state where the condition is not met
        system_state = {"reservoir": MockStatefulComponent({"level": 9})}
        controller.step(system_state, dt=1)
        self.assertEqual(controller.get_state(), {"command": 0})

    def test_multi_condition_rule(self):
        rules = [
            {
                "if": [
                    {"variable": "reservoir.state.level", "operator": ">", "value": 10},
                    {"variable": "pump.state.status", "operator": "==", "value": "off"}
                ],
                "then": {"command": "start_pump"}
            }
        ]
        default_actions = {"command": "do_nothing"}
        controller = RuleBasedOperationalController(rules=rules, default_actions=default_actions)

        # Both conditions met
        system_state = {
            "reservoir": MockStatefulComponent({"level": 12}),
            "pump": MockStatefulComponent({"status": "off"})
        }
        controller.step(system_state, dt=1)
        self.assertEqual(controller.get_state(), {"command": "start_pump"})

        # First condition not met
        system_state = {
            "reservoir": MockStatefulComponent({"level": 8}),
            "pump": MockStatefulComponent({"status": "off"})
        }
        controller.step(system_state, dt=1)
        self.assertEqual(controller.get_state(), {"command": "do_nothing"})

        # Second condition not met
        system_state = {
            "reservoir": MockStatefulComponent({"level": 12}),
            "pump": MockStatefulComponent({"status": "on"})
        }
        controller.step(system_state, dt=1)
        self.assertEqual(controller.get_state(), {"command": "do_nothing"})

    def test_default_action(self):
        rules = [
            {
                "if": [{"variable": "reservoir.state.level", "operator": ">", "value": 10}],
                "then": {"command": 1}
            }
        ]
        default_actions = {"command": 0}
        controller = RuleBasedOperationalController(rules=rules, default_actions=default_actions)

        # Condition not met, should use default action
        system_state = {"reservoir": MockStatefulComponent({"level": 5})}
        controller.step(system_state, dt=1)
        self.assertEqual(controller.get_state(), {"command": 0})

    def test_rule_priority(self):
        rules = [
            {
                "if": [{"variable": "reservoir.state.level", "operator": ">", "value": 15}],
                "then": {"command": "high_alert"}
            },
            {
                "if": [{"variable": "reservoir.state.level", "operator": ">", "value": 10}],
                "then": {"command": "medium_alert"}
            }
        ]
        default_actions = {"command": "no_alert"}
        controller = RuleBasedOperationalController(rules=rules, default_actions=default_actions)

        # Both conditions are met, but the first rule should be triggered
        system_state = {"reservoir": MockStatefulComponent({"level": 16})}
        controller.step(system_state, dt=1)
        self.assertEqual(controller.get_state(), {"command": "high_alert"})

        # Only the second condition is met
        system_state = {"reservoir": MockStatefulComponent({"level": 12})}
        controller.step(system_state, dt=1)
        self.assertEqual(controller.get_state(), {"command": "medium_alert"})

        # No conditions are met
        system_state = {"reservoir": MockStatefulComponent({"level": 8})}
        controller.step(system_state, dt=1)
        self.assertEqual(controller.get_state(), {"command": "no_alert"})

if __name__ == '__main__':
    unittest.main()
