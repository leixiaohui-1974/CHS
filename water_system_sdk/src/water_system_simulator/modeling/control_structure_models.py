import numpy as np
from typing import Optional
from .base_model import BaseModel
from .actuator_models import ActuatorBase

class GateBase(ActuatorBase):
    """
    Base class for gate models.
    """
    def __init__(self, gate_width: float, discharge_coeff: float, initial_opening: float = 0.0, **kwargs):
        super().__init__(initial_position=initial_opening, **kwargs)
        self.gate_width = gate_width
        self.discharge_coeff = discharge_coeff
        self.g = 9.81
        self.flow = 0.0
        self.output = self.flow

    def set_opening(self, height: float):
        """
        Set the target opening height of the gate.
        """
        self.set_target(height)

    def step(self, upstream_level: float, downstream_level: float, dt: float, **kwargs):
        """
        Updates the gate's state and calculates flow.
        Must be implemented by subclasses.
        """
        raise NotImplementedError

    def get_current_opening(self) -> float:
        """Returns the current opening height."""
        return self.get_current_position()


class SluiceGate(GateBase):
    """
    Represents a vertical sluice gate, automatically switching between
    free-flow and submerged-flow discharge equations.
    """
    def step(self, upstream_level: float, downstream_level: float, dt: float, **kwargs):
        """
        Calculates flow based on upstream/downstream levels and gate opening.
        """
        # Update actuator position first
        self.update(dt)
        gate_opening = self.get_current_position()
        gate_opening = max(0, gate_opening)

        # Ensure upstream level is above the channel bottom (assumed 0)
        h1 = max(0, upstream_level)
        h2 = max(0, downstream_level)

        if gate_opening <= 0 or h1 <= h2:
            self.flow = 0.0
            self.output = self.flow
            return self.output

        # Determine if flow is free or submerged
        # A common criterion is to compare downstream depth to the gate opening
        if h2 > gate_opening: # Submerged orifice flow
            head_diff = h1 - h2
            if head_diff <= 0:
                self.flow = 0.0
            else:
                area = self.gate_width * gate_opening
                self.flow = self.discharge_coeff * area * np.sqrt(2 * self.g * head_diff)
        else: # Free weir flow
            area = self.gate_width * gate_opening
            # Using the formula for a rectangular sharp-crested weir under a sluice
            # Q = C_d * b * a * sqrt(2 * g * h1)
            self.flow = self.discharge_coeff * area * np.sqrt(2 * self.g * h1)

        self.output = self.flow
        return self.output


class RadialGate(GateBase):
    """
    Represents a radial (or Tainter) gate.
    Uses a specific discharge formula for this gate type.
    """
    def __init__(self, gate_width: float, discharge_coeff: float, pivot_height: float, trunnion_radius: float, initial_opening: float = 0.0, **kwargs):
        super().__init__(gate_width=gate_width, discharge_coeff=discharge_coeff, initial_opening=initial_opening, **kwargs)
        self.pivot_height = pivot_height # Height of the pivot above the channel floor
        self.trunnion_radius = trunnion_radius # Radius of the gate's arc

    def step(self, upstream_level: float, downstream_level: float, dt: float, **kwargs):
        """
        Calculates flow for a radial gate.
        Note: The formula can be complex. This is a common simplification.
        The 'opening' is interpreted as the angle in radians for this gate type.
        """
        # Update actuator position first
        self.update(dt)
        gate_opening_angle = self.get_current_position() # Here, position is angle in radians
        gate_opening_angle = max(0, gate_opening_angle)

        h1 = max(0, upstream_level)

        if gate_opening_angle <= 0 or h1 <= downstream_level:
            self.flow = 0.0
            self.output = self.flow
            return self.output

        # The formula for radial gates is often given as Q = C_d * W * h_gate * sqrt(2*g*H_eff)
        # where h_gate is the vertical opening, which depends on the angle.
        # h_gate = r * (1 - cos(theta)) - this is incorrect, it's just h_gate = r * sin(theta)
        # A better model uses effective opening height based on angle
        h_gate = self.trunnion_radius * np.sin(gate_opening_angle)

        if h_gate <= 0:
            self.flow = 0.0
        else:
            # Effective head is approximately the upstream water level for free flow
            self.flow = self.discharge_coeff * self.gate_width * h_gate * np.sqrt(2 * self.g * h1)

        self.output = self.flow
        return self.output

class PumpStationModel(BaseModel):
    """
    Represents a pump station with one or more pumps operating in parallel.
    The pump's performance is defined by a characteristic curve (head vs. flow).
    """
    def __init__(self, num_pumps_total: int, curve_coeffs: list, initial_num_pumps_on: int = 1, **kwargs):
        """
        Initializes the Pump Station model.

        Args:
            num_pumps_total (int): Total number of pumps in the station.
            curve_coeffs (list): For Flow = a*Head^2 + b*Head + c.
            initial_num_pumps_on (int, optional): Number of pumps initially running.
        """
        super().__init__(**kwargs)
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
        return float(max(0, flow))

    def step(self, inlet_pressure: float, outlet_pressure: float, num_pumps_on: Optional[int] = None, **kwargs):
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
    def __init__(self, max_flow_area: float, discharge_coeff: float, efficiency: float, **kwargs):
        """
        Initializes the Hydropower Station model.

        Args:
            max_flow_area (float): Max flow area through the turbine (m^2).
            discharge_coeff (float): Discharge coefficient (dimensionless).
            efficiency (float): Overall efficiency of the turbine-generator set.
        """
        super().__init__(**kwargs)
        self.max_flow_area = max_flow_area
        self.discharge_coeff = discharge_coeff
        self.efficiency = efficiency
        self.g = 9.81
        self.rho = 1000
        self.flow = 0.0
        self.power = 0.0
        self.output = self.flow

    def step(self, upstream_level: float, downstream_level: float, vane_opening: float, **kwargs):
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
