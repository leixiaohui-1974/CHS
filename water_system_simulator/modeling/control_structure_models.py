import numpy as np
from .base_model import BaseModel

class GateModel(BaseModel):
    """
    Represents a gate using the orifice flow equation.
    """
    def __init__(self, discharge_coefficient, area):
        """
        Initializes the gate model.

        Args:
            discharge_coefficient (float): The discharge coefficient of the gate.
            area (float): The area of the gate opening.
        """
        self.discharge_coefficient = discharge_coefficient
        self.area = area
        self.g = 9.81  # acceleration due to gravity
        self.flow = 0.0 # Initial flow

    def step(self, upstream_level, downstream_level, area):
        """
        Calculates the flow through the gate for the current time step.

        Args:
            upstream_level (float): The water level upstream of the gate.
            downstream_level (float): The water level downstream of the gate.
            area (float): The area of the gate opening.

        Returns:
            float: The flow rate through the gate.
        """
        self.area = area # Update area state
        head_diff = upstream_level - downstream_level
        if head_diff <= 0 or self.area <=0:
            self.flow = 0.0
            return 0.0

        self.flow = self.discharge_coefficient * self.area * np.sqrt(2 * self.g * head_diff)
        return self.flow

class PumpModel(BaseModel):
    """
    Represents a pump with a simple characteristic curve.
    """
    def __init__(self, max_flow, max_head):
        """
        Initializes the pump model.

        Args:
            max_flow (float): The maximum flow rate of the pump.
            max_head (float): The maximum head the pump can overcome.
        """
        self.max_flow = max_flow
        self.max_head = max_head
        self.output = 0.0

    def step(self, head_diff, speed):
        """
        Calculates the flow rate of the pump.

        Args:
            head_diff (float): The head difference the pump is working against.
            speed (float): The speed of the pump (0 to 1).

        Returns:
            float: The flow rate of the pump.
        """
        if speed <= 0:
            self.output = 0.0
            return 0.0

        # Simple linear pump curve
        flow = self.max_flow * (1 - head_diff / self.max_head) * speed

        self.output = max(0.0, flow)
        return self.output

class GateStationModel(BaseModel):
    """
    Represents a station with multiple gates.
    """
    def __init__(self, number_of_gates: int, gate_configs: list):
        """
        Initializes the Gate Station model.

        Args:
            number_of_gates (int): The number of gates in the station.
            gate_configs (list): A list of dictionaries, each containing the
                                 properties for a single GateModel.
                                 e.g., [{'discharge_coefficient': 0.6, 'area': 1.0}, ...]
        """
        if number_of_gates != len(gate_configs):
            raise ValueError("Number of gates must match the length of gate_configs.")

        self.gates = [GateModel(**config) for config in gate_configs]
        self.output = 0.0 # Total flow

    def step(self, upstream_level: float, downstream_level: float, areas: list):
        """
        Calculates the total flow through all gates in the station.

        Args:
            upstream_level (float): The water level upstream of the station.
            downstream_level (float): The water level downstream of the station.
            areas (list): A list of areas for each gate opening.

        Returns:
            float: The total flow rate through the station.
        """
        if len(areas) != len(self.gates):
            raise ValueError("The number of areas provided must match the number of gates.")

        total_flow = 0.0
        for i, gate in enumerate(self.gates):
            total_flow += gate.step(upstream_level, downstream_level, areas[i])

        self.output = total_flow
        return self.output

class HydropowerStationModel(BaseModel):
    """
    Represents a simple hydropower station.
    """
    def __init__(self, rated_flow: float, rated_head: float, efficiency: float = 0.90):
        """
        Initializes the Hydropower Station model.

        Args:
            rated_flow (float): The flow rate at the rated operating point (m^3/s).
            rated_head (float): The head at the rated operating point (m).
            efficiency (float, optional): The efficiency of the turbine-generator unit. Defaults to 0.90.
        """
        # Calculate a simplified discharge coefficient from rated values
        # Q = C * sqrt(H) => C = Q_rated / sqrt(H_rated)
        if rated_head <= 0:
            raise ValueError("Rated head must be positive.")
        self.flow_coeff = rated_flow / np.sqrt(rated_head)
        self.efficiency = efficiency

        self.g = 9.81
        self.rho = 1000 # water density in kg/m^3

        self.output = 0.0 # Flow
        self.power_generation = 0.0

    def step(self, upstream_level: float, downstream_level: float, guide_vane_opening: float):
        """
        Calculates the outflow and power generation.

        Args:
            upstream_level (float): The upstream water level (m).
            downstream_level (float): The downstream water level (m).
            guide_vane_opening (float): The opening of the guide vanes (0 to 1).

        Returns:
            float: The outflow from the station (m^3/s).
        """
        head_diff = upstream_level - downstream_level
        guide_vane_opening = np.clip(guide_vane_opening, 0, 1)

        if head_diff <= 0 or guide_vane_opening <= 0:
            self.output = 0.0
            self.power_generation = 0.0
            return 0.0

        # Calculate flow
        flow = self.flow_coeff * guide_vane_opening * np.sqrt(head_diff)
        self.output = flow

        # Calculate power
        # P = eta * rho * g * Q * H
        power = self.efficiency * self.rho * self.g * flow * head_diff
        self.power_generation = power / 1e6 # Convert from W to MW

        return self.output

class PumpStationModel(BaseModel):
    """
    Represents a station with multiple pumps.
    """
    def __init__(self, number_of_pumps: int, pump_configs: list):
        """
        Initializes the Pump Station model.

        Args:
            number_of_pumps (int): The number of pumps in the station.
            pump_configs (list): A list of dictionaries, each containing the
                                 properties for a single PumpModel.
                                 e.g., [{'max_flow': 10, 'max_head': 20}, ...]
        """
        if number_of_pumps != len(pump_configs):
            raise ValueError("Number of pumps must match the length of pump_configs.")

        self.pumps = [PumpModel(**config) for config in pump_configs]
        self.output = 0.0 # Total flow

    def step(self, head_diff: float, speeds: list):
        """
        Calculates the total flow from all pumps in the station.

        Args:
            head_diff (float): The head difference the station is working against.
            speeds (list): A list of speeds for each pump (0 to 1).

        Returns:
            float: The total flow rate from the station.
        """
        if len(speeds) != len(self.pumps):
            raise ValueError("The number of speeds provided must match the number of pumps.")

        total_flow = 0.0
        for i, pump in enumerate(self.pumps):
            total_flow += pump.step(head_diff, speeds[i])

        self.output = total_flow
        return self.output
