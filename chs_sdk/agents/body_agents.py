from .base import BaseAgent, Message
from water_system_sdk.src.water_system_simulator.modeling.storage_models import ReservoirModel
from water_system_sdk.src.water_system_simulator.modeling.control_structure_models import GateModel, PumpStationModel


class TankAgent(BaseAgent):
    """
    An agent that encapsulates a water tank (reservoir) model.
    """
    def __init__(self, agent_id, message_bus, area, initial_level, max_level=20.0):
        super().__init__(agent_id, message_bus)
        self.model = ReservoirModel(area=area, initial_level=initial_level, max_level=max_level)
        self.subscribe(f"tank/{self.agent_id}/inflow")
        self.subscribe(f"tank/{self.agent_id}/release_outflow")
        self.subscribe(f"tank/{self.agent_id}/demand_outflow")

    def execute(self, dt=1.0):
        """
        Runs one step of the reservoir simulation.
        """
        self.model.step(dt)
        self.publish(f"tank/{self.agent_id}/state", self.model.get_state())

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
    def __init__(self, agent_id, message_bus, num_gates, gate_width, discharge_coeff):
        super().__init__(agent_id, message_bus)
        self.model = GateModel(num_gates=num_gates, gate_width=gate_width, discharge_coeff=discharge_coeff)
        self.upstream_level = 0
        self.downstream_level = 0
        self.gate_opening = 0
        self.subscribe(f"tank/{agent_id.replace('gate', 'tank')}/state") # a bit of a hack
        self.subscribe(f"gate/{self.agent_id}/downstream_level")
        self.subscribe(f"gate/{self.agent_id}/opening")


    def execute(self, dt=1.0):
        """
        Runs one step of the gate simulation.
        """
        self.model.step(self.upstream_level, self.downstream_level, self.gate_opening)
        self.publish(f"gate/{self.agent_id}/state", self.model.get_state())

    def on_message(self, message: Message):
        """
        Handles incoming messages to update the gate's inputs.
        """
        if message.topic == f"tank/{self.agent_id.replace('gate', 'tank')}/state":
            self.upstream_level = message.payload.get("level", 0)
        elif message.topic == f"gate/{self.agent_id}/downstream_level":
            self.downstream_level = message.payload.get("value", 0)
        elif message.topic == f"gate/{self.agent_id}/opening":
            self.gate_opening = message.payload.get("value", 0)


class ValveAgent(GateAgent):
    """
    An agent that encapsulates a valve model.
    For now, it uses the GateModel as a stand-in.
    """
    pass


class PumpAgent(BaseAgent):
    """
    An agent that encapsulates a pump station model.
    """
    def __init__(self, agent_id, message_bus, num_pumps_total, curve_coeffs, initial_num_pumps_on=1):
        super().__init__(agent_id, message_bus)
        self.model = PumpStationModel(
            num_pumps_total=num_pumps_total,
            curve_coeffs=curve_coeffs,
            initial_num_pumps_on=initial_num_pumps_on
        )
        self.inlet_pressure = 0
        self.outlet_pressure = 0
        self.num_pumps_on = initial_num_pumps_on
        self.subscribe(f"pump/{self.agent_id}/inlet_pressure")
        self.subscribe(f"pump/{self.agent_id}/outlet_pressure")
        self.subscribe(f"pump/{self.agent_id}/num_pumps_on")

    def execute(self, dt=1.0):
        """
        Runs one step of the pump station simulation.
        """
        self.model.step(self.inlet_pressure, self.outlet_pressure, self.num_pumps_on)
        self.publish(f"pump/{self.agent_id}/state", self.model.get_state())

    def on_message(self, message: Message):
        """
        Handles incoming messages to update the pump's inputs.
        """
        if message.topic == f"pump/{self.agent_id}/inlet_pressure":
            self.inlet_pressure = message.payload.get("value", 0)
        elif message.topic == f"pump/{self.agent_id}/outlet_pressure":
            self.outlet_pressure = message.payload.get("value", 0)
        elif message.topic == f"pump/{self.agent_id}/num_pumps_on":
            self.num_pumps_on = message.payload.get("value", 1)
