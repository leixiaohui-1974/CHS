import numpy as np
from .base_model import BaseModel
from .pump_models import PumpBase, PositiveDisplacementPump
from .actuator_models import ActuatorBase
from typing import List, Dict, Callable

class StationBase(BaseModel):
    """
    Base class for a station, which is a container for other components.
    It manages the components and their interactions.
    """
    def __init__(self, components: List[BaseModel], **kwargs):
        super().__init__(**kwargs)
        self.components = {comp.name: comp for comp in components}

    def get_component(self, name: str) -> BaseModel:
        return self.components.get(name)

    def step(self, dt: float, **kwargs):
        # The step logic for a station depends on its type.
        # It might involve running component steps in a certain order,
        # or implementing control logic for them.
        raise NotImplementedError

class AuxiliarySystem:
    """
    A simple model for auxiliary systems (e.g., cooling, HVAC) in a station.
    """
    def __init__(self, base_power_draw: float, operational_power_draw: float):
        self.base_power_draw = base_power_draw # Constant power draw
        self.operational_power_draw = operational_power_draw # Power draw when station is active
        self.power = self.base_power_draw
        self.is_active = False

    def update(self, is_active: bool):
        self.is_active = is_active
        if self.is_active:
            self.power = self.base_power_draw + self.operational_power_draw
        else:
            self.power = self.base_power_draw

class PumpingStation(StationBase):
    """
    A pumping station containing one or more pumps.
    Manages parallel operation and simple control logic.
    """
    def __init__(self, pumps: List[PumpBase], auxiliary_system: AuxiliarySystem = None, **kwargs):
        super().__init__(components=pumps, **kwargs)
        self.pumps = pumps # Keep a typed reference
        self.aux_system = auxiliary_system if auxiliary_system else AuxiliarySystem(0,0)
        self.total_flow = 0.0
        self.total_power = 0.0
        self.output = self.total_flow

    def step(self, system_head: float, dt: float, **kwargs):
        """
        Steps each pump and aggregates the flow.
        A more advanced version would have complex scheduling logic.
        """
        self.total_flow = 0.0
        self.total_power = 0.0
        any_pump_on = False

        for pump in self.pumps:
            pump.step(system_head=system_head, dt=dt)
            self.total_flow += pump.flow
            self.total_power += pump.power
            if pump.get_current_speed() > 0:
                any_pump_on = True

        self.aux_system.update(any_pump_on)
        self.total_power += self.aux_system.power

        self.output = self.total_flow
        return self.output

    def get_state(self):
        """Returns the aggregated state of the pumping station."""
        return {
            "total_flow": self.total_flow,
            "total_power": self.total_power,
            "auxiliary_power": self.aux_system.power,
            "component_states": {p.name: p.get_state() for p in self.pumps}
        }

# Process-Specific Actuators

class ChemicalDosingPump(PositiveDisplacementPump):
    """
    A specialized positive displacement pump for chemical dosing.
    The key difference is in the interpretation of its output (e.g., L/hr of chemical).
    Functionally, it's the same as a PositiveDisplacementPump.
    """
    def __init__(self, rated_flow_L_per_hr: float, **kwargs):
        # Convert to m^3/s for internal consistency
        rated_flow_m3_per_s = rated_flow_L_per_hr / (1000 * 3600)
        super().__init__(rated_flow=rated_flow_m3_per_s, **kwargs)
        self.output_units = "L/hr"

    def get_flow_L_per_hr(self):
        return self.flow * 3600 * 1000

class Blower(ActuatorBase):
    """
    A model for a blower, used in aeration processes.
    Calculates air flow based on speed and discharge pressure.
    """
    def __init__(self, flow_curve: Callable[[float, float], float], **kwargs):
        """
        Args:
            flow_curve (Callable): A function that takes (speed_ratio, pressure_kpa) and returns flow (m3/s).
        """
        super().__init__(**kwargs)
        self.flow_curve = flow_curve
        self.flow = 0.0

    def step(self, discharge_pressure_kpa: float, dt: float, **kwargs):
        self.update(dt)
        speed = self.get_current_position()

        if speed <= 0:
            self.flow = 0.0
        else:
            self.flow = self.flow_curve(speed, discharge_pressure_kpa)

        self.output = self.flow
        return self.output
