from .base import BaseAgent, Message
from water_system_sdk.src.water_system_simulator.control.pid_controller import PIDController
from water_system_sdk.src.water_system_simulator.control.mpc_controller import MPCController


class PIDAgent(BaseAgent):
    """
    An agent that encapsulates a PID controller.
    """
    def __init__(self, agent_id, message_bus, Kp, Ki, Kd, set_point,
                 input_topic, output_topic, output_min=None, output_max=None):
        super().__init__(agent_id, message_bus)
        self.controller = PIDController(Kp=Kp, Ki=Ki, Kd=Kd, set_point=set_point,
                                        output_min=output_min, output_max=output_max)
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.subscribe(self.input_topic)
        self.current_value = 0

    def execute(self, dt=1.0):
        """
        Runs one step of the PID control calculation.
        """
        control_action = self.controller.step(dt, error_source=self.current_value)
        self.publish(self.output_topic, {"value": control_action})

    def on_message(self, message: Message):
        """
        Handles incoming messages to update the PID controller's input.
        """
        if message.topic == self.input_topic:
            self.current_value = message.payload.get("value", 0)


class MPCAgent(BaseAgent):
    """
    An agent that encapsulates an MPC controller.
    This is a placeholder for future implementation.
    """
    def __init__(self, agent_id, message_bus, model, horizon, input_topic, output_topic):
        super().__init__(agent_id, message_bus)
        # The MPC controller from the SDK is more complex to initialize.
        # This is a simplified placeholder.
        # self.controller = MPCController(model=model, horizon=horizon)
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.subscribe(self.input_topic)
        self.current_state = None
        print("Warning: MPCAgent is a placeholder and not fully implemented.")

    def execute(self, dt=1.0):
        """
        Runs one step of the MPC control calculation.
        """
        # Placeholder logic
        if self.current_state is not None:
            # In a real implementation, you would call the MPC controller's step method.
            # control_action = self.controller.step(self.current_state)
            control_action = 0 # Dummy action
            self.publish(self.output_topic, {"value": control_action})
            print(f"MPC Agent {self.agent_id} would have computed a control action.")


    def on_message(self, message: Message):
        """
        Handles incoming messages to update the MPC controller's state.
        """
        if message.topic == self.input_topic:
            self.current_state = message.payload # MPC might need the full state dictionary
            print(f"MPC Agent {self.agent_id} received state: {self.current_state}")
