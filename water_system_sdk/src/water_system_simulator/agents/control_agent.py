from .base_agent import BaseEmbodiedAgent
from chs_sdk.agents.message import MacroCommandMessage
from ..control.pid_controller import PIDController
from ..control.gs_mpc_controller import GainScheduledMPCController
from ..control.kalman_adaptive_mpc_controller import KalmanAdaptiveMPCController
import numpy as np

class ControlAgent(BaseEmbodiedAgent):
    """
    Represents a "decision and action" system for a control object like
    a gate, pump, or valve. It can host various control algorithms.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.algorithm = None
        self.target_trajectory = None
        self.current_command = None
        self.load_algorithm(kwargs.get("control_algorithm", "PID"), kwargs.get("algorithm_config", {}))

    def load_algorithm(self, algorithm_name: str, config: dict):
        """
        Loads a control algorithm based on its name and configuration.
        """
        if algorithm_name == "PID":
            self.algorithm = PIDController(**config)
        elif algorithm_name == "GainScheduledPID":
            # Placeholder for Gain-Scheduled PID
            print("WARNING: GainScheduledPID not implemented, using standard PID.")
            self.algorithm = PIDController(**config)
        elif algorithm_name == "AdaptiveMPC":
            # Placeholder for Adaptive MPC
            self.algorithm = KalmanAdaptiveMPCController(**config)
        else:
            raise ValueError(f"Unknown control algorithm: {algorithm_name}")
        print(f"INFO: Loaded algorithm '{algorithm_name}' for agent {self.name}.")

    def on_message(self, message: MacroCommandMessage):
        """
        Receives and interprets a macro command, converting it into a target trajectory.
        """
        print(f"INFO: {self.name} received macro command: {message}")
        # This is a simplified conversion. A real implementation would be more complex.
        num_steps = int(message.duration_hours * 3600 / self.get_simulation_dt())
        self.target_trajectory = np.linspace(self.get_current_value(), message.target_value, num_steps)
        print(f"INFO: Target trajectory generated with {num_steps} steps.")

    def step(self, dt: float, **kwargs):
        """
        Executes one step of the control logic.
        """
        if self.algorithm is None:
            print(f"WARNING: No control algorithm loaded for {self.name}.")
            return

        # Get current state from sensors (passed in kwargs)
        current_state = kwargs.get("current_state", {})

        # Get setpoint for the current step
        if self.target_trajectory is not None and len(self.target_trajectory) > 0:
            setpoint = self.target_trajectory[0]
            self.target_trajectory = self.target_trajectory[1:]
        else:
            # If no trajectory, maintain current setpoint (or a default)
            setpoint = self.algorithm.setpoint

        # Update the setpoint in the algorithm
        self.algorithm.set_point = setpoint
        # Calculate control command
        self.current_command = self.algorithm.step(dt, current_state.get(self.name))

        # The command would be sent to an actuator in a real system.
        # For now, we just store it.
        print(f"INFO: {self.name} calculated command: {self.current_command}")

    # Helper methods to be implemented or connected to the simulation environment
    def get_simulation_dt(self):
        return 1.0 # Placeholder

    def get_current_value(self):
        return 0.0 # Placeholder
