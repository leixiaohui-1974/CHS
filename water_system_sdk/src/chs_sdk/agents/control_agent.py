from .base_agent import BaseAgent
from .message import MacroCommandMessage, StateUpdateMessage, Message
from ..control.pid_controller import PIDController
from ..control.gs_mpc_controller import GainScheduledMPCController
from ..control.kalman_adaptive_mpc_controller import KalmanAdaptiveMPCController
import numpy as np

class ControlAgent(BaseAgent):
    """
    Represents a "decision and action" system for a control object like
    a gate, pump, or valve. It subscribes to state updates from a target
    agent and uses a control algorithm to calculate commands.
    """
    def __init__(self, agent_id: str, kernel: 'AgentKernel', **config):
        super().__init__(agent_id, kernel, **config)
        self.algorithm = None
        self.target_trajectory = None
        self.current_command = None

        # New properties for state subscription
        self.target_agent_id = config.get("target_agent_id")
        self.variable_to_control = config.get("variable_to_control")
        self.latest_state = {}

        if not self.target_agent_id or not self.variable_to_control:
            raise ValueError("ControlAgent requires 'target_agent_id' and 'variable_to_control' in its config.")

        self.load_algorithm(config.get("control_algorithm", "PID"), config.get("algorithm_config", {}))

    def setup(self):
        """Subscribes to the state updates from the target agent."""
        super().setup()
        subscription_topic = f"state/update/{self.target_agent_id}"
        self.kernel.message_bus.subscribe(self, subscription_topic)
        # Also subscribe to macro commands, perhaps on a specific topic
        self.kernel.message_bus.subscribe(self, f"command/{self.agent_id}")

    def load_algorithm(self, algorithm_name: str, config: dict):
        """Loads a control algorithm based on its name and configuration."""
        if algorithm_name == "PID":
            self.algorithm = PIDController(**config)
        elif algorithm_name == "GainScheduledPID":
            self.algorithm = PIDController(**config) # Placeholder
        elif algorithm_name == "AdaptiveMPC":
            self.algorithm = KalmanAdaptiveMPCController(**config)
        else:
            raise ValueError(f"Unknown control algorithm: {algorithm_name}")

    def on_message(self, message: Message):
        """Handles incoming state updates and macro commands."""
        if isinstance(message, StateUpdateMessage):
            # Update the latest known state from the body agent
            self.latest_state = message.payload
        elif isinstance(message, MacroCommandMessage):
            # This part is complex and needs a better way to get the current value
            # For now, we'll use the latest state if available
            current_value = self.latest_state.get(self.variable_to_control, 0.0)
            num_steps = int(message.duration_hours * 3600 / self.kernel.time_step)
            self.target_trajectory = np.linspace(current_value, message.target_value, num_steps)
        else:
            # Handle other message types if necessary
            pass

    def on_execute(self, current_time: float, time_step: float):
        """Executes one step of the control logic."""
        if self.algorithm is None:
            return

        # Get the feedback signal from the last received state update
        feedback_signal = self.latest_state.get(self.variable_to_control)
        if feedback_signal is None:
            # No state update received yet, cannot proceed
            return

        # Get setpoint for the current step from the trajectory
        if self.target_trajectory is not None and len(self.target_trajectory) > 0:
            setpoint = self.target_trajectory[0]
            self.target_trajectory = self.target_trajectory[1:]
        else:
            setpoint = self.algorithm.setpoint

        # Update the algorithm and calculate the command
        self.algorithm.set_point = setpoint
        self.current_command = self.algorithm.step(dt=time_step, feedback_signal=feedback_signal)

        # In a real system, this command would be published to an actuator agent
        # self._publish(f"actuator/{self.target_agent_id}", {"command": self.current_command})
