from chs_sdk.agents.base import BaseAgent
from chs_sdk.agents.message import Message
from chs_sdk.modules.modeling.instrument_models import SensorBase
import inspect

class EulerMethod:
    """
    A simple implementation of the forward Euler method for solving ODEs.
    y_{n+1} = y_n + dt * f(t_n, y_n)
    """
    def __init__(self, f, dt):
        """
        Initializes the Euler solver.
        Args:
            f (callable): The function to integrate, f(t, y).
            dt (float): The time step.
        """
        self.f = f
        self.dt = dt

    def step(self, t, y):
        """
        Performs a single step of the Euler method.
        Args:
            t (float): The current time.
            y (float): The current value of y.
        Returns:
            float: The new value of y after one time step.
        """
        return y + self.dt * self.f(t, y)


class LevelSensor(SensorBase):
    """
    A concrete sensor class for measuring water level.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.output = 0.0

    def step(self, true_value, dt, **kwargs):
        self.output = self.measure(true_value, dt)
        return self.output

    def get_state(self):
        return {'output': self.output}


class ModelAgent(BaseAgent):
    """
    A generic agent that wraps a simulation model to make it compatible
    with the new AgentKernel. It handles the lifecycle of the model and
    the communication via the message bus.
    """
    def __init__(self, agent_id, kernel, model_class, **config):
        super().__init__(agent_id, kernel, **config)
        self.model = model_class(**config)
        self.subscriptions = {}
        self.input_values = {} # Store the latest values from subscriptions
        self.output_topic = f"{self.agent_id}/output"

    def on_execute(self, current_time, time_step, extra_state=None):
        # 1. Set inputs on the model's 'input' attribute if it exists
        if hasattr(self.model, 'input'):
            for key, value in self.input_values.items():
                if hasattr(self.model.input, key):
                    setattr(self.model.input, key, value)

        # 2. Prepare arguments for the step method
        step_args = self.input_values.copy()
        step_args['t'] = current_time
        step_args['dt'] = time_step

        system_state = self.kernel._agents.copy()
        if extra_state:
            system_state.update(extra_state)
        step_args['system_state'] = system_state

        # 3. Filter args to match the model's step method signature
        print(f"[{self.agent_id}] step_args: {step_args}")
        step_params = inspect.signature(self.model.step).parameters
        filtered_args = {k: v for k, v in step_args.items() if k in step_params}
        print(f"[{self.agent_id}] filtered_args: {filtered_args}")

        # 4. Call the step method
        self.model.step(**filtered_args)

        # 5. Publish output
        if hasattr(self.model, 'get_state') and callable(self.model.get_state):
            output = self.model.get_state()
            if isinstance(output, dict):
                for key, value in output.items():
                    self._publish(f"{self.agent_id}/{key}", value)
            elif output is not None:
                self._publish(self.output_topic, output)
        elif hasattr(self.model, 'output'):
            self._publish(self.output_topic, self.model.output)

    def on_message(self, message: Message):
        if message.topic in self.subscriptions:
            port_name = self.subscriptions[message.topic]
            self.input_values[port_name] = message.payload

    def subscribe(self, topic, port_name):
        self.subscriptions[topic] = port_name
        self.kernel.message_bus.subscribe(self, topic)

    def __getattr__(self, name):
        # Delegate attribute access to the underlying model.
        return getattr(self.model, name)


class SimpleDispatchAgent(BaseAgent):
    def __init__(self, agent_id, kernel, dispatch_logic, **kwargs):
        super().__init__(agent_id, kernel, **kwargs)
        self.dispatch_logic = dispatch_logic

    def on_execute(self, current_time, time_step):
        if current_time in self.dispatch_logic:
            command = self.dispatch_logic[current_time]
            self._publish(command.topic, command.payload)
