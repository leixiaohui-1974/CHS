from .base_agent import BaseAgent
from .message import Message
from water_system_sdk.src.water_system_simulator.modeling.storage_models import ReservoirModel
from water_system_sdk.src.water_system_simulator.modeling.control_structure_models import GateModel, PumpStationModel


class TankAgent(BaseAgent):
    """
    An agent that encapsulates a water tank (reservoir) model.
    """
    def __init__(self, agent_id, kernel, area, initial_level, max_level=20.0, **kwargs):
        super().__init__(agent_id, kernel, **kwargs)
        self.model = ReservoirModel(area=area, initial_level=initial_level, max_level=max_level)

    def setup(self):
        """
        Subscribe to the necessary topics.
        """
        self.kernel.message_bus.subscribe(f"tank/{self.agent_id}/inflow", self)
        self.kernel.message_bus.subscribe(f"tank/{self.agent_id}/release_outflow", self)
        self.kernel.message_bus.subscribe(f"tank/{self.agent_id}/demand_outflow", self)

    def execute(self, current_time: float):
        """
        Runs one step of the reservoir simulation.
        """
        time_step = self.kernel.time_step if hasattr(self.kernel, 'time_step') else 1.0
        self.model.step(time_step)
        self._publish(f"tank/{self.agent_id}/state", self.model.get_state())

    def on_message(self, message: Message):
        """
        Handles incoming messages to update the tank's inputs.
        """
        if message.topic == f"tank/{self.agent_id}/inflow":
            self.model.input.inflow = message.payload.get("value", 0)
        elif message.topic == f"tank/{self.agent_id}/release_outflow":
            self.model.input.release_outflow = message.payload.get("value", 0)
        elif message.topic == f"tank/{self.agent_id}/demand_outflow":
            self.model.input.demand_outflow = message.payload.get("value", 0)


class GateAgent(BaseAgent):
    """
    An agent that encapsulates a gate model.
    """
    def __init__(self, agent_id, kernel, num_gates, gate_width, discharge_coeff,
                 upstream_topic, downstream_topic, opening_topic, state_topic, **kwargs):
        super().__init__(agent_id, kernel, **kwargs)
        self.model = GateModel(
            num_gates=num_gates,
            gate_width=gate_width,
            discharge_coeff=discharge_coeff
        )
        self.upstream_topic = upstream_topic
        self.downstream_topic = downstream_topic
        self.opening_topic = opening_topic
        self.state_topic = state_topic

        self.upstream_level = 0.0
        self.downstream_level = 0.0
        self.gate_opening = 0.0

    def setup(self):
        """
        Subscribe to the necessary topics for gate operation.
        """
        self.kernel.message_bus.subscribe(self.upstream_topic, self)
        self.kernel.message_bus.subscribe(self.downstream_topic, self)
        self.kernel.message_bus.subscribe(self.opening_topic, self)

    def execute(self, current_time: float):
        """
        Runs one step of the gate simulation.
        """
        self.model.step(self.upstream_level, self.downstream_level, self.gate_opening)
        self._publish(self.state_topic, self.model.get_state())

    def on_message(self, message: Message):
        """
        Handles incoming messages to update the gate's inputs.
        """
        if message.topic == self.upstream_topic:
            self.upstream_level = message.payload.get("level", message.payload.get("output", 0.0))
        elif message.topic == self.downstream_topic:
            self.downstream_level = message.payload.get("level", message.payload.get("output", 0.0))
        elif message.topic == self.opening_topic:
            self.gate_opening = message.payload.get("value", 0.0)


class ValveAgent(BaseAgent):
    """
    An agent that encapsulates a valve, modeled using the GateModel logic.
    It operates on its own topics for inputs and outputs.
    """
    def __init__(self, agent_id, kernel, num_gates, gate_width, discharge_coeff,
                 upstream_topic, downstream_topic, opening_topic, state_topic, **kwargs):
        super().__init__(agent_id, kernel, **kwargs)
        self.model = GateModel(
            num_gates=num_gates,
            gate_width=gate_width,
            discharge_coeff=discharge_coeff
        )
        self.upstream_topic = upstream_topic
        self.downstream_topic = downstream_topic
        self.opening_topic = opening_topic
        self.state_topic = state_topic

        self.upstream_level = 0.0
        self.downstream_level = 0.0
        self.gate_opening = 0.0

    def setup(self):
        """
        Subscribe to the necessary topics for valve operation.
        """
        self.kernel.message_bus.subscribe(self.upstream_topic, self)
        self.kernel.message_bus.subscribe(self.downstream_topic, self)
        self.kernel.message_bus.subscribe(self.opening_topic, self)

    def execute(self, current_time: float):
        """
        Runs one step of the valve simulation.
        """
        self.model.step(self.upstream_level, self.downstream_level, self.gate_opening)
        self._publish(self.state_topic, self.model.get_state())

    def on_message(self, message: Message):
        """
        Handles incoming messages to update the valve's inputs.
        """
        if message.topic == self.upstream_topic:
            self.upstream_level = message.payload.get("level", message.payload.get("output", 0.0))
        elif message.topic == self.downstream_topic:
            self.downstream_level = message.payload.get("level", message.payload.get("output", 0.0))
        elif message.topic == self.opening_topic:
            self.gate_opening = message.payload.get("value", 0.0)


class PumpAgent(BaseAgent):
    """
    An agent that encapsulates a pump station model.
    """
    def __init__(self, agent_id, kernel, num_pumps_total, curve_coeffs,
                 inlet_pressure_topic, outlet_pressure_topic, num_pumps_on_topic, state_topic,
                 initial_num_pumps_on=1, **kwargs):
        super().__init__(agent_id, kernel, **kwargs)
        self.model = PumpStationModel(
            num_pumps_total=num_pumps_total,
            curve_coeffs=curve_coeffs,
            initial_num_pumps_on=initial_num_pumps_on
        )
        self.inlet_pressure_topic = inlet_pressure_topic
        self.outlet_pressure_topic = outlet_pressure_topic
        self.num_pumps_on_topic = num_pumps_on_topic
        self.state_topic = state_topic

        self.inlet_pressure = 0.0
        self.outlet_pressure = 0.0
        self.num_pumps_on = initial_num_pumps_on

    def setup(self):
        """
        Subscribe to the necessary topics for pump operation.
        """
        self.kernel.message_bus.subscribe(self.inlet_pressure_topic, self)
        self.kernel.message_bus.subscribe(self.outlet_pressure_topic, self)
        self.kernel.message_bus.subscribe(self.num_pumps_on_topic, self)

    def execute(self, current_time: float):
        """
        Runs one step of the pump station simulation.
        """
        self.model.step(self.inlet_pressure, self.outlet_pressure, self.num_pumps_on)
        self._publish(self.state_topic, self.model.get_state())

    def on_message(self, message: Message):
        """
        Handles incoming messages to update the pump's inputs.
        """
        if message.topic == self.inlet_pressure_topic:
            self.inlet_pressure = message.payload.get("value", 0.0)
        elif message.topic == self.outlet_pressure_topic:
            self.outlet_pressure = message.payload.get("value", 0.0)
        elif message.topic == self.num_pumps_on_topic:
            self.num_pumps_on = message.payload.get("value", 1)
