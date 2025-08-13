import numpy as np
from .base_model import BaseModel

class GateModel(BaseModel):
    """
    Represents a gate using the orifice flow equation.
    """
    def __init__(self, discharge_coefficient, area):
        self.discharge_coefficient = discharge_coefficient
        self.area = area
        self.g = 9.81
        self.flow = 0.0
        self.output = 0.0

    def step(self, upstream_level, downstream_level, area):
        self.area = area
        head_diff = upstream_level - downstream_level
        if head_diff <= 0 or self.area <= 0:
            self.flow = 0.0
        else:
            self.flow = self.discharge_coefficient * self.area * np.sqrt(2 * self.g * head_diff)
        self.output = self.flow
        return self.output

    def get_state(self):
        return {"flow": self.flow, "area": self.area}

class PumpModel(BaseModel):
    """
    Represents a pump with a simple characteristic curve.
    """
    def __init__(self, max_flow, max_head):
        self.max_flow = max_flow
        self.max_head = max_head
        self.output = 0.0

    def step(self, head_diff, speed):
        if speed <= 0:
            self.output = 0.0
        else:
            flow = self.max_flow * (1 - head_diff / self.max_head) * speed
            self.output = max(0.0, flow)
        return self.output

    def get_state(self):
        return {"flow": self.output}

class GateStationModel(BaseModel):
    """
    Represents a station with multiple gates.
    """
    def __init__(self, number_of_gates: int, gate_configs: list):
        if number_of_gates != len(gate_configs):
            raise ValueError("Number of gates must match the length of gate_configs.")
        self.gates = [GateModel(**config) for config in gate_configs]
        self.output = 0.0

    def step(self, upstream_level: float, downstream_level: float, areas: list):
        if len(areas) != len(self.gates):
            raise ValueError("The number of areas provided must match the number of gates.")
        total_flow = sum(gate.step(upstream_level, downstream_level, areas[i]) for i, gate in enumerate(self.gates))
        self.output = total_flow
        return self.output

    def get_state(self):
        return {"total_flow": self.output, "gate_areas": [g.area for g in self.gates]}

class HydropowerStationModel(BaseModel):
    """
    Represents a simple hydropower station.
    """
    def __init__(self, rated_flow: float, rated_head: float, efficiency: float = 0.90):
        if rated_head <= 0:
            raise ValueError("Rated head must be positive.")
        self.flow_coeff = rated_flow / np.sqrt(rated_head)
        self.efficiency = efficiency
        self.g = 9.81
        self.rho = 1000
        self.output = 0.0
        self.power_generation = 0.0

    def step(self, upstream_level: float, downstream_level: float, guide_vane_opening: float):
        head_diff = upstream_level - downstream_level
        guide_vane_opening = np.clip(guide_vane_opening, 0, 1)
        if head_diff <= 0 or guide_vane_opening <= 0:
            self.output = 0.0
            self.power_generation = 0.0
        else:
            flow = self.flow_coeff * guide_vane_opening * np.sqrt(head_diff)
            self.output = flow
            power = self.efficiency * self.rho * self.g * flow * head_diff
            self.power_generation = power / 1e6
        return self.output

    def get_state(self):
        return {"flow": self.output, "power_generation_MW": self.power_generation}

class PumpStationModel(BaseModel):
    """
    Represents a station with multiple pumps.
    """
    def __init__(self, number_of_pumps: int, pump_configs: list):
        if number_of_pumps != len(pump_configs):
            raise ValueError("Number of pumps must match the length of pump_configs.")
        self.pumps = [PumpModel(**config) for config in pump_configs]
        self.output = 0.0

    def step(self, head_diff: float, speeds: list):
        if len(speeds) != len(self.pumps):
            raise ValueError("The number of speeds provided must match the number of pumps.")
        total_flow = sum(pump.step(head_diff, speeds[i]) for i, pump in enumerate(self.pumps))
        self.output = total_flow
        return self.output

    def get_state(self):
        return {"total_flow": self.output}
