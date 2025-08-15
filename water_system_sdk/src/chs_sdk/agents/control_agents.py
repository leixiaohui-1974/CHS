from .base_agent import BaseAgent
from .message import Message
from water_system_sdk.src.water_system_simulator.control.pid_controller import PIDController
from water_system_sdk.src.water_system_simulator.control.mpc_controller import MPCController


class PIDAgent(BaseAgent):
    """
    An agent that encapsulates a PID controller.
    """
    def __init__(self, agent_id, kernel, Kp, Ki, Kd, set_point,
                 input_topic, output_topic, output_min=None, output_max=None, **kwargs):
        super().__init__(agent_id, kernel, **kwargs)
        self.controller = PIDController(Kp=Kp, Ki=Ki, Kd=Kd, set_point=set_point,
                                        output_min=output_min, output_max=output_max)
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.current_value = 0

    def setup(self):
        """
        Subscribe to the necessary topics.
        """
        self.kernel.message_bus.subscribe(self.input_topic, self)

    def execute(self, current_time: float):
        """
        Runs one step of the PID control calculation.
        """
        time_step = self.kernel.time_step if hasattr(self.kernel, 'time_step') else 1.0
        # The PID controller expects the process variable, not the error source
        # The controller calculates the error internally (set_point - process_variable)
        control_action = self.controller.step(time_step, self.current_value)
        self._publish(self.output_topic, {"value": control_action})

    def on_message(self, message: Message):
        """
        Handles incoming messages to update the PID controller's input.
        """
        if message.topic == self.input_topic:
            # The tank state is a dictionary, we need the 'level'
            self.current_value = message.payload.get("level", 0)


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
