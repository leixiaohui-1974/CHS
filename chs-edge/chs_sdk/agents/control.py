from chs_sdk.modules.control import PIDController


class PIDControlAgent:
    """
    A mock implementation of the PIDControlAgent for the MVP.
    """
    def __init__(self, agent_id: str, pid_instance: PIDController):
        self.agent_id = agent_id
        self.pid = pid_instance
        print(f"[MOCK SDK] PIDControlAgent '{self.agent_id}' initialized.")

    def execute(self, observation: dict) -> dict:
        """
        Executes the agent's logic based on an observation.
        """
        current_level = observation.get('current_level')
        dt = observation.get('dt', 1)  # Default dt to 1 if not provided

        if current_level is None:
            print("[MOCK SDK] Error: 'current_level' not found in observation.")
            return {'error': 'current_level not in observation'}

        # Get the control variable from the PID controller
        control_variable = self.pid.calculate(current_level, dt)

        # For the MVP, we'll assume this agent controls a valve.
        # The action is a dictionary that can be sent to the hardware driver.
        action = {'valve_position': control_variable}
        return action
