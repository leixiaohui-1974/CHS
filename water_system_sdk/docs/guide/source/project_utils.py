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
        # 设置传感器参数，减少噪声和偏差
        kwargs.setdefault('noise_stddev', 0.0)  # 无噪声
        kwargs.setdefault('bias', 0.0)          # 无偏差
        kwargs.setdefault('drift', 0.0)         # 无漂移
        kwargs.setdefault('lag', 0.0)           # 无滞后
        super().__init__(**kwargs)
        self.output = 0.0

    def step(self, true_value=0.0, dt=1.0, **kwargs):
        self.output = self.measure(true_value, dt)
        return self.output

    def get_state(self):
        return {'output': self.output}


class EnhancedModelAgent(BaseAgent):
    """
    增强版ModelAgent，支持对有**kwargs参数的step方法传递所有参数
    专门用于解决LinearTank等模型需要通过kwargs接收参数的问题
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

        # 3. Enhanced parameter filtering - 支持kwargs参数
        print(f"[{self.agent_id}] step_args: {step_args}")
        step_params = inspect.signature(self.model.step).parameters
        print(f"[{self.agent_id}] step method expects: {list(step_params.keys())}")
        
        # 检查step方法是否有**kwargs参数
        has_kwargs = any(param.kind == inspect.Parameter.VAR_KEYWORD for param in step_params.values())
        
        if has_kwargs:
            # 如果有**kwargs，传递所有参数
            filtered_args = step_args
            print(f"[{self.agent_id}] Model has **kwargs, passing all args")
        else:
            # 否则只传递匹配的参数
            filtered_args = {k: v for k, v in step_args.items() if k in step_params}
            
        print(f"[{self.agent_id}] filtered_args: {filtered_args}")

        # 4. Call the step method
        self.model.step(**filtered_args)

        # 5. Publish output
        if hasattr(self.model, 'get_state') and callable(self.model.get_state):
            output = self.model.get_state()
            print(f"[{self.agent_id}] get_state() returned: {output}")
            if isinstance(output, dict):
                for key, value in output.items():
                    print(f"[{self.agent_id}] Publishing {key}={value} to topic '{self.agent_id}/{key}'")
                    self._publish(f"{self.agent_id}/{key}", value)
                    # 如果是storage字段，也发布为true_value（用于传感器）
                    if key == 'storage':
                        print(f"[{self.agent_id}] Also publishing storage as true_value")
                        self._publish(f"{self.agent_id}/true_value", value)
                    # 如果是actual_position字段，也发布为inflow（用于水库）
                    if key == 'actual_position' and hasattr(self.model, 'flow'):
                        print(f"[{self.agent_id}] Also publishing flow as inflow")
                        self._publish(f"{self.agent_id}/inflow", self.model.flow)
            elif output is not None:
                print(f"[{self.agent_id}] Publishing output={output} to topic '{self.output_topic}'")
                self._publish(self.output_topic, output)
        elif hasattr(self.model, 'output'):
            print(f"[{self.agent_id}] Publishing model.output={self.model.output} to topic '{self.output_topic}'")
            self._publish(self.output_topic, self.model.output)
            # 如果是闸门，也发布为inflow（用于水库）
            if hasattr(self.model, 'flow'):
                print(f"[{self.agent_id}] Also publishing flow as inflow")
                self._publish(f"{self.agent_id}/inflow", self.model.flow)
            # 如果是PID控制器，也发布output
            if hasattr(self.model, 'output'):
                print(f"[{self.agent_id}] Also publishing output")
                self._publish(f"{self.agent_id}/output", self.model.output)

    def on_message(self, message: Message):
        print(f"[{self.agent_id}] Received message: topic='{message.topic}' payload={message.payload}")
        if message.topic in self.subscriptions:
            port_name = self.subscriptions[message.topic]
            self.input_values[port_name] = message.payload
            print(f"[{self.agent_id}] Stored as {port_name}={message.payload}")
        else:
            print(f"[{self.agent_id}] Topic '{message.topic}' not in subscriptions: {list(self.subscriptions.keys())}")

    def subscribe(self, topic, port_name):
        self.subscriptions[topic] = port_name
        self.kernel.message_bus.subscribe(self, topic)

    def __getattr__(self, name):
        # Delegate attribute access to the underlying model.
        return getattr(self.model, name)


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
        print(f"[{self.agent_id}] step method expects: {list(step_params.keys())}")
        filtered_args = {k: v for k, v in step_args.items() if k in step_params}
        print(f"[{self.agent_id}] filtered_args: {filtered_args}")

        # 4. Call the step method
        self.model.step(**filtered_args)

        # 5. Publish output
        if hasattr(self.model, 'get_state') and callable(self.model.get_state):
            output = self.model.get_state()
            print(f"[{self.agent_id}] get_state() returned: {output}")
            if isinstance(output, dict):
                for key, value in output.items():
                    print(f"[{self.agent_id}] Publishing {key}={value} to topic '{self.agent_id}/{key}'")
                    self._publish(f"{self.agent_id}/{key}", value)
                    # 如果是storage字段，也发布为true_value（用于传感器）
                    if key == 'storage':
                        print(f"[{self.agent_id}] Also publishing storage as true_value")
                        self._publish(f"{self.agent_id}/true_value", value)
                    # 如果是actual_position字段，也发布为inflow（用于水库）
                    if key == 'actual_position' and hasattr(self.model, 'flow'):
                        print(f"[{self.agent_id}] Also publishing flow as inflow")
                        self._publish(f"{self.agent_id}/inflow", self.model.flow)
            elif output is not None:
                print(f"[{self.agent_id}] Publishing output={output} to topic '{self.output_topic}'")
                self._publish(self.output_topic, output)
        elif hasattr(self.model, 'output'):
            print(f"[{self.agent_id}] Publishing model.output={self.model.output} to topic '{self.output_topic}'")
            self._publish(self.output_topic, self.model.output)
            # 如果是闸门，也发布为inflow（用于水库）
            if hasattr(self.model, 'flow'):
                print(f"[{self.agent_id}] Also publishing flow as inflow")
                self._publish(f"{self.agent_id}/inflow", self.model.flow)
            # 如果是PID控制器，也发布output
            if hasattr(self.model, 'output'):
                print(f"[{self.agent_id}] Also publishing output")
                self._publish(f"{self.agent_id}/output", self.model.output)

    def on_message(self, message: Message):
        print(f"[{self.agent_id}] Received message: topic='{message.topic}' payload={message.payload}")
        if message.topic in self.subscriptions:
            port_name = self.subscriptions[message.topic]
            self.input_values[port_name] = message.payload
            print(f"[{self.agent_id}] Stored as {port_name}={message.payload}")
        else:
            print(f"[{self.agent_id}] Topic '{message.topic}' not in subscriptions: {list(self.subscriptions.keys())}")

    def subscribe(self, topic, port_name):
        self.subscriptions[topic] = port_name
        self.kernel.message_bus.subscribe(self, topic)

    def __getattr__(self, name):
        # Delegate attribute access to the underlying model.
        return getattr(self.model, name)


class ReservoirModelAgent(BaseAgent):
    """
    专门用于水库模型的智能体，能够正确发布水位信息
    """
    def __init__(self, agent_id, kernel, model_class, **config):
        super().__init__(agent_id, kernel, **config)
        self.model = model_class(**config)
        self.subscriptions = {}
        self.input_values = {} # Store the latest values from subscriptions
        self.output_topic = f"{self.agent_id}/output"
        # 获取水库面积，用于计算水位
        self.reservoir_area = config.get('reservoir_area', 1000.0)

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
        print(f"[{self.agent_id}] step method expects: {list(step_params.keys())}")
        filtered_args = {k: v for k, v in step_args.items() if k in step_params}
        print(f"[{self.agent_id}] filtered_args: {filtered_args}")

        # 4. Call the step method
        self.model.step(**filtered_args)

        # 5. Publish output - 水库模型特殊处理
        if hasattr(self.model, 'get_state') and callable(self.model.get_state):
            output = self.model.get_state()
            print(f"[{self.agent_id}] get_state() returned: {output}")
            if isinstance(output, dict):
                for key, value in output.items():
                    print(f"[{self.agent_id}] Publishing {key}={value} to topic '{self.agent_id}/{key}'")
                    self._publish(f"{self.agent_id}/{key}", value)
                    
                    # 水库模型特殊处理：将蓄水量转换为水位
                    if key == 'storage':
                        # 计算水位 = 蓄水量 / 水库面积
                        water_level = value / self.reservoir_area
                        print(f"[{self.agent_id}] Publishing water_level={water_level} to topic '{self.agent_id}/water_level'")
                        self._publish(f"{self.agent_id}/water_level", water_level)
                        
                        # 同时发布为true_value（用于传感器）
                        print(f"[{self.agent_id}] Also publishing water_level as true_value")
                        self._publish(f"{self.agent_id}/true_value", water_level)
                        
                        # 也发布蓄水量（保持向后兼容）
                        print(f"[{self.agent_id}] Also publishing storage as storage_value")
                        self._publish(f"{self.agent_id}/storage_value", value)
            elif output is not None:
                print(f"[{self.agent_id}] Publishing output={output} to topic '{self.output_topic}'")
                self._publish(self.output_topic, output)
        elif hasattr(self.model, 'output'):
            print(f"[{self.agent_id}] Publishing model.output={self.model.output} to topic '{self.output_topic}'")
            self._publish(self.output_topic, self.model.output)

    def on_message(self, message: Message):
        print(f"[{self.agent_id}] Received message: topic='{message.topic}' payload={message.payload}")
        if message.topic in self.subscriptions:
            port_name = self.subscriptions[message.topic]
            self.input_values[port_name] = message.payload
            print(f"[{self.agent_id}] Stored as {port_name}={message.payload}")
        else:
            print(f"[{self.agent_id}] Topic '{message.topic}' not in subscriptions: {list(self.subscriptions.keys())}")

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
