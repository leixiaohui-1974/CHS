from .base import BaseAgent
from .message import Message
from ..utils.logger import log

class PIDAgent(BaseAgent):
    """
    A standalone agent that implements a PID controller.
    The entire PID logic is contained within this agent.
    It waits for an initial measurement before starting control calculations.
    """
    def __init__(self, agent_id, kernel, Kp, Ki, Kd, set_point,
                 input_topic, output_topic,
                 output_min=None, output_max=None, **kwargs):
        """
        Initializes the PIDAgent.
        """
        super().__init__(agent_id, kernel, **kwargs)
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.set_point = set_point
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.output_min = output_min
        self.output_max = output_max

        # Internal state variables
        self._integral = 0.0
        self._previous_error = 0.0
        self._current_value = 0.0
        self.initialized = False # Flag to wait for first measurement

    def setup(self):
        """
        Subscribe to the input topic to receive process variable updates.
        """
        self.kernel.message_bus.subscribe(self, self.input_topic)

    def on_message(self, message: Message):
        """
        Handles an incoming measurement message.
        Initializes the controller on the first valid message.
        """
        if message.topic == self.input_topic:
            new_value = message.payload.get("level", message.payload.get("value"))
            if new_value is not None:
                self._current_value = new_value
                if not self.initialized:
                    # Use the first measurement to initialize the previous_error
                    # to prevent a large derivative kick on the first run.
                    self._previous_error = self.set_point - self._current_value
                    self.initialized = True
                    log.info(f"PIDAgent '{self.agent_id}' initialized with first measurement: {self._current_value}")

    def execute(self, current_time: float):
        """
        Calculates the control output based on the PID algorithm, but only after
        it has been initialized with a measurement.
        """
        # Guard clause: Do not run the controller until initialized.
        if not self.initialized:
            return

        dt = self.kernel.time_step
        if dt <= 0:
            return

        error = self.set_point - self._current_value

        # --- Calculate integral term with anti-windup ---
        potential_integral = self._integral + error * dt

        # --- Calculate derivative term ---
        derivative = (error - self._previous_error) / dt

        # --- Calculate unbounded output ---
        output = self.Kp * error + self.Ki * potential_integral + self.Kd * derivative

        # --- Clamp output and apply anti-windup ---
        clamped_output = output
        if self.output_max is not None and clamped_output > self.output_max:
            clamped_output = self.output_max
        if self.output_min is not None and clamped_output < self.output_min:
            clamped_output = self.output_min

        if output == clamped_output:
             self._integral = potential_integral

        # --- Update state for the next time step ---
        self._previous_error = error

        # --- Publish the control action ---
        self._publish(self.output_topic, {"value": clamped_output})


import numpy as np
import cvxpy as cp
from chs_sdk.legacy.modeling.base_model import BaseModel
from chs_sdk.legacy.control.mpc_controller import MPCController

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
        self.kernel.message_bus.subscribe(self, self.state_topic)
        if self.disturbance_topic:
            self.kernel.message_bus.subscribe(self, self.disturbance_topic)

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
