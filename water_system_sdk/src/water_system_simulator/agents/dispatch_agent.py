from chs_sdk.agents.base_agent import BaseAgent
from chs_sdk.agents.message import Message, MacroCommandMessage
import numpy as np

class DispatchAgent(BaseAgent):
    """
    The strategic "brain" of the water system. It performs long-term
    optimization and responds to emergencies.
    """
    def __init__(self, agent_id, kernel, **kwargs):
        super().__init__(agent_id, kernel, **kwargs)
        self.system_model = None # A high-level model of the entire system
        self.optimization_horizon_hours = 24
        self.control_agents = kwargs.get("control_agents", [])

    def setup(self):
        """
        The DispatchAgent may need to subscribe to high-level topics
        or perform initial model loading here in the future.
        """
        pass

    def on_message(self, message: Message):
        """
        Handles incoming messages, such as situational awareness or alarms.
        """
        if "awareness" in message.topic:
            self.process_awareness_update(message.payload)
        elif "alarm" in message.topic:
            self.trigger_emergency_response(message.payload)

    def execute(self, current_time: float):
        """
        The main execution loop for the DispatchAgent.
        """
        self.step(dt=self.kernel.time_step, simulation_time=current_time)

    def run_long_term_optimization(self):
        """
        Runs a long-term MPC-style optimization to generate macro commands.
        """
        print("INFO: Running long-term optimization...")
        # This is a placeholder for a complex optimization process.
        # In a real system, this would involve:
        # 1. Getting the current system state.
        # 2. Getting forecasts (e.g., demand, weather).
        # 3. Running an MPC solver against the high-level system model.
        # 4. Generating a sequence of MacroCommands.

        # Placeholder: Generate a simple command for each control agent.
        commands = []
        for agent_name in self.control_agents:
            command = MacroCommandMessage(
                target_variable=f"{agent_name}.level",
                target_value=np.random.uniform(2.0, 3.0), # Random target
                duration_hours=6,
                strategy="slow_transition"
            )
            commands.append({"recipient": agent_name, "command": command})

        print(f"INFO: Optimization complete. Generated {len(commands)} macro commands.")
        return commands

    def trigger_emergency_response(self, alarm_payload: dict):
        """
        Generates an immediate response to a critical alarm.
        """
        print(f"CRITICAL: Emergency alarm received: {alarm_payload}. Triggering response.")
        # This is a placeholder for rule-based or model-based emergency logic.
        # Example: If pressure is too high, command a valve to close.

        # Placeholder: Generate a command to a specific agent.
        emergency_command = MacroCommandMessage(
            target_variable="pressure_relief_valve.setting",
            target_value=0.0, # Open valve
            duration_hours=1,
            strategy="immediate"
        )
        commands = [{"recipient": "ControlAgent_Pressure_1", "command": emergency_command}]

        print(f"INFO: Emergency response generated.")
        return commands

    def step(self, dt: float, **kwargs):
        """
        The main execution loop for the DispatchAgent.
        This would likely be run on a slower timescale than other agents.
        """
        # In a real system, this might be triggered by a timer (e.g., every hour)
        # or by specific events.

        # For simulation purposes, let's assume it runs its optimization once.
        if kwargs.get("simulation_time", 0) % 3600 == 0: # Run once per hour
            macro_commands = self.run_long_term_optimization()
            print(f"DEBUG: Dispatching commands: {macro_commands}")
            for command_info in macro_commands:
                recipient = command_info["recipient"]
                command = command_info["command"]
                # Infer topic from publishes_to list based on agent name
                try:
                    # e.g., pid_controller_1 -> cmd.macro.control_tank_1
                    agent_index = self.control_agents.index(recipient)
                    topic = self.config.get("publishes_to", [])[agent_index]
                    self._publish(topic, command.dict())
                    print(f"INFO: DispatchAgent published command to {recipient} on topic {topic}")
                except (ValueError, IndexError) as e:
                    print(f"ERROR: Could not find topic for recipient {recipient}: {e}")

        print(f"INFO: DispatchAgent {self.agent_id} is stepping.")
