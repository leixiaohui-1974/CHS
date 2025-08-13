import numpy as np
from .base_model import BaseModel

class GateStationModel(BaseModel):
    """
    Represents a station with multiple identical sluice gates.
    Calculates flow based on the gate opening and upstream water level.
    """
    def __init__(self, num_gates: int, gate_width: float, discharge_coeff: float):
        """
        Initializes the Gate Station model.

        Args:
            num_gates (int): The number of identical gates in the station.
            gate_width (float): The width of a single gate (m).
            discharge_coeff (float): The discharge coefficient for the gates (dimensionless).
        """
        super().__init__()
        self.num_gates = num_gates
        self.gate_width = gate_width
        self.discharge_coeff = discharge_coeff
        self.g = 9.81
        self.flow = 0.0
        self.output = self.flow

    def step(self, upstream_level: float, gate_opening: float):
        """
        Calculates the total flow for the next time step.

        Args:
            upstream_level (float): The water level upstream of the gate (m).
            gate_opening (float): The height of the gate opening (m).
        """
        gate_opening = np.clip(gate_opening, 0, np.inf)
        if upstream_level <= 0 or gate_opening <= 0:
            self.flow = 0.0
        else:
            area_per_gate = self.gate_width * gate_opening
            flow_per_gate = self.discharge_coeff * area_per_gate * np.sqrt(2 * self.g * upstream_level)
            self.flow = flow_per_gate * self.num_gates
        self.output = self.flow

    def get_state(self):
        return {"flow": self.flow, "output": self.output}

class PumpStationModel(BaseModel):
    """
    Represents a pump station with one or more pumps operating in parallel.
    The pump's performance is defined by a characteristic curve (head vs. flow).
    """
    def __init__(self, num_pumps_total: int, curve_coeffs: list, initial_num_pumps_on: int = 1):
        """
        Initializes the Pump Station model.

        Args:
            num_pumps_total (int): Total number of pumps in the station.
            curve_coeffs (list): For Flow = a*Head^2 + b*Head + c.
            initial_num_pumps_on (int, optional): Number of pumps initially running.
        """
        super().__init__()
        if len(curve_coeffs) != 3:
            raise ValueError("curve_coeffs must be a list of 3 numbers [a, b, c].")
        self.num_pumps_total = num_pumps_total
        self.curve_coeffs = np.array(curve_coeffs)
        self.num_pumps_on = initial_num_pumps_on
        self.flow = 0.0
        self.output = self.flow

    def _calculate_flow_per_pump(self, head_diff: float) -> float:
        a, b, c = self.curve_coeffs
        if head_diff < 0: head_diff = 0
        flow = a * head_diff**2 + b * head_diff + c
        return max(0, flow)

    def step(self, inlet_pressure: float, outlet_pressure: float, num_pumps_on: int = None):
        """
        Calculates the total flow for the next time step.
        """
        if num_pumps_on is not None:
            self.num_pumps_on = np.clip(int(num_pumps_on), 0, self.num_pumps_total)
        head_diff = outlet_pressure - inlet_pressure
        flow_per_pump = self._calculate_flow_per_pump(head_diff)
        self.flow = flow_per_pump * self.num_pumps_on
        self.output = self.flow

    def get_state(self):
        return {"flow": self.flow, "num_pumps_on": self.num_pumps_on, "output": self.output}


class HydropowerStationModel(BaseModel):
    """
    Represents a hydropower station.
    Calculates outflow and power generation based on head and guide vane opening.
    """
    def __init__(self, max_flow_area: float, discharge_coeff: float, efficiency: float):
        """
        Initializes the Hydropower Station model.

        Args:
            max_flow_area (float): Max flow area through the turbine (m^2).
            discharge_coeff (float): Discharge coefficient (dimensionless).
            efficiency (float): Overall efficiency of the turbine-generator set.
        """
        super().__init__()
        self.max_flow_area = max_flow_area
        self.discharge_coeff = discharge_coeff
        self.efficiency = efficiency
        self.g = 9.81
        self.rho = 1000
        self.flow = 0.0
        self.power = 0.0
        self.output = self.flow

    def step(self, upstream_level: float, downstream_level: float, vane_opening: float):
        """
        Calculates the outflow and power generation for the next time step.
        """
        vane_opening = np.clip(vane_opening, 0.0, 1.0)
        head = upstream_level - downstream_level
        if head <= 0:
            self.flow = 0.0
            self.power = 0.0
        else:
            effective_area = self.max_flow_area * vane_opening
            self.flow = self.discharge_coeff * effective_area * np.sqrt(2 * self.g * head)
            self.power = self.efficiency * self.rho * self.g * self.flow * head
        self.output = self.flow

    def get_state(self):
        return {"flow": self.flow, "power": self.power, "output": self.output}
