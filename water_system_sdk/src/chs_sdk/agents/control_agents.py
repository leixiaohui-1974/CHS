from .base_agent import BaseAgent
from .message import Message, MacroCommandMessage
from water_system_sdk.src.water_system_simulator.control.pid_controller import PIDController
from water_system_sdk.src.water_system_simulator.control.mpc_controller import MPCController


class PIDAgent(BaseAgent):
    """
    An agent that encapsulates a PID controller.
    It can receive dynamic setpoint updates from a macro command topic.
    """
    def __init__(self, agent_id, kernel, Kp, Ki, Kd,
                 subscribes_to: list, publishes_to: str,
                 set_point=0.0, output_min=None, output_max=None, **kwargs):
        super().__init__(agent_id, kernel, **kwargs)
        self.controller = PIDController(Kp=Kp, Ki=Ki, Kd=Kd, set_point=set_point,
                                        output_min=output_min, output_max=output_max)
        self.subscribes_to = subscribes_to
        self.publishes_to = publishes_to
        self.current_value = 0
        self.macro_command_topic = None
        self.sensor_topic = None

        # New attributes for handling trajectories
        self.setpoint_trajectory = None
        self.current_trajectory_step = 0

    def setup(self):
        """
        Subscribe to the necessary topics.
        """
        if not isinstance(self.subscribes_to, list) or len(self.subscribes_to) < 2:
            raise ValueError("PIDAgent 'subscribes_to' must be a list of at least two topics.")

        self.macro_command_topic = self.subscribes_to[0]
        self.sensor_topic = self.subscribes_to[1]

        self.kernel.message_bus.subscribe(self, self.macro_command_topic)
        self.kernel.message_bus.subscribe(self, self.sensor_topic)

    def execute(self, current_time: float):
        """
        Runs one step of the PID control calculation.
        Uses a setpoint from a trajectory if available.
        """
        if self.setpoint_trajectory and self.current_trajectory_step < len(self.setpoint_trajectory):
            current_setpoint = self.setpoint_trajectory[self.current_trajectory_step]
            self.controller.set_point = current_setpoint
            self.current_trajectory_step += 1
        else:
            # Fallback to the default setpoint if no trajectory
            current_setpoint = self.config.get('setpoint', 0)
            self.controller.set_point = current_setpoint

        time_step = self.kernel.time_step if hasattr(self.kernel, 'time_step') else 1.0
        control_action = self.controller.step(time_step, self.current_value)
        self._publish(self.publishes_to, {"value": control_action})

    def on_message(self, message: Message):
        """
        Handles incoming messages to update the PID controller's input or setpoint.
        """
        if message.topic == self.sensor_topic:
            self.current_value = message.payload.get("level", 0)
        elif message.topic == self.macro_command_topic:
            try:
                # The payload should be a dict that can be parsed into a MacroCommandMessage
                macro_command = MacroCommandMessage(**message.payload)
                print(f"PIDAgent ({self.agent_id}) received macro command: {macro_command}")
                self._translate_macro_command(macro_command)
            except Exception as e:
                print(f"ERROR: PIDAgent {self.agent_id} failed to parse MacroCommandMessage: {e}")

    def _translate_macro_command(self, command: MacroCommandMessage):
        """
        Translates a macro command into a concrete setpoint trajectory.
        This is a simplified linear interpolation implementation.
        """
        current_setpoint = self.controller.set_point
        target_setpoint = command.target_value

        # Ensure kernel and time_step are available
        if not hasattr(self.kernel, 'time_step') or self.kernel.time_step <= 0:
             print(f"ERROR: PIDAgent {self.agent_id} cannot generate trajectory without a valid kernel time_step.")
             self.setpoint_trajectory = [target_setpoint]
             return

        duration_steps = int(command.duration_hours * 3600 / self.kernel.time_step)

        if duration_steps > 0:
            self.setpoint_trajectory = [
                current_setpoint + (target_setpoint - current_setpoint) * i / duration_steps
                for i in range(duration_steps + 1)
            ]
        else:
            self.setpoint_trajectory = [target_setpoint]

        self.current_trajectory_step = 0
        print(f"PIDAgent ({self.agent_id}) generated new setpoint trajectory with {len(self.setpoint_trajectory)} steps.")



import numpy as np
import cvxpy as cp
from water_system_sdk.src.water_system_simulator.modeling.base_model import BaseModel

class MPCAgent(BaseAgent):
    """
    An agent that encapsulates a Model Predictive Control (MPC) controller.
    """
    def __init__(self, agent_id, kernel, prediction_model: BaseModel,
                 prediction_horizon: int, control_horizon: int, set_point: float,
                 q_weight: float, r_weight: float, u_min: float, u_max: float,
                 state_topic: str, disturbance_topic: str, output_topic: str, **kwargs):
        super().__init__(agent_id, kernel, **kwargs)

        self.controller = MPCController(
            prediction_model=prediction_model,
            prediction_horizon=prediction_horizon,
            control_horizon=control_horizon,
            set_point=set_point,
            q_weight=q_weight,
            r_weight=r_weight,
            u_min=u_min,
            u_max=u_max
        )
        self.state_topic = state_topic
        self.disturbance_topic = disturbance_topic
        self.output_topic = output_topic

        self.current_state = 0.0
        self.disturbance_forecast = np.array([])

    def setup(self):
        """
        Subscribe to the necessary topics.
        """
        self.kernel.message_bus.subscribe(self.state_topic, self)
        if self.disturbance_topic:
            self.kernel.message_bus.subscribe(self.disturbance_topic, self)

    def execute(self, current_time: float):
        """
        Runs one step of the MPC control calculation.
        """
        control_action = self.controller.step(
            current_state=self.current_state,
            disturbance_forecast=self.disturbance_forecast
        )
        self._publish(self.output_topic, {"value": control_action})

    def on_message(self, message: Message):
        """
        Handles incoming messages to update the MPC controller's state.
        """
        if message.topic == self.state_topic:
            # Assuming the state message has a 'level' or 'output' key
            self.current_state = message.payload.get("level", message.payload.get("output", 0.0))
        elif message.topic == self.disturbance_topic:
            # Assuming the disturbance message has a 'forecast' key
            self.disturbance_forecast = np.array(message.payload.get("forecast", []))
