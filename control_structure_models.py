"""
Core models for hydraulic control structures and composite station models.

This module provides a set of classes to simulate various components of a
water management system, including gates, pumps, and turbines, as well as
the stations that contain them. The design emphasizes modularity and
extensibility through the use of abstract base classes.
"""
from __future__ import annotations

import numpy as np
from abc import ABC, abstractmethod
from typing import List, Union, Dict, Any, Optional

# Forward reference for type hint to avoid circular import
if False:
    from disturbance_models import ActuatorFault

# Constants
GRAVITY = 9.81  # m/s^2
WATER_DENSITY = 1000  # kg/m^3


class ControllableStructure(ABC):
    """
    Abstract base class for any controllable hydraulic structure.

    This class defines the universal interface for all controllable elements
    in the water system simulation, such as gates, valves, pumps, or turbines.
    """

    def __init__(self, name: str):
        self.name = name
        self._current_flow_rate: float = 0.0
        self.simulation_time: float = 0.0 # Current time for fault checking

    @property
    def current_flow_rate(self) -> float:
        """Get the current flow rate through the structure in m^3/s."""
        return self._current_flow_rate

    @abstractmethod
    def update_state(self, simulation_time: float, *args, **kwargs) -> None:
        """
        Update the structure's state, including its flow rate.

        This method should be called at each simulation step. The arguments
        will vary depending on the specific structure type, but will typically
        include upstream and downstream water levels or head.
        """
        self.simulation_time = simulation_time


# --- Gate Models ---

class BaseGate(ControllableStructure):
    """
    Abstract base class for all types of gates and valves.
    """

    def __init__(self, name: str, width: float, discharge_coeff: float = 0.62, actuator_fault: Optional['ActuatorFault'] = None):
        super().__init__(name)
        self.width = width
        self.discharge_coeff = discharge_coeff
        self._opening_percentage: float = 0.0  # 0.0 = fully closed, 100.0 = fully open
        self.actuator_fault = actuator_fault

    @property
    def opening_percentage(self) -> float:
        """Get the current gate opening as a percentage (0-100)."""
        return self._opening_percentage

    @opening_percentage.setter
    def opening_percentage(self, value: float) -> None:
        """Set the gate opening percentage, subject to actuator faults."""
        commanded_value = max(0.0, min(100.0, value))
        if self.actuator_fault:
            self._opening_percentage = self.actuator_fault.apply(commanded_value, self.simulation_time)
        else:
            self._opening_percentage = commanded_value

    def _calculate_flow(self, upstream_head: float, downstream_head: float) -> float:
        """Calculates flow using the orifice equation, assuming free-flow."""
        head_diff = upstream_head - downstream_head
        if head_diff <= 0 or self.opening_percentage <= 0:
            return 0.0

        effective_opening_height = (self.opening_percentage / 100.0) * upstream_head
        area = self.width * effective_opening_height

        flow = self.discharge_coeff * area * np.sqrt(2 * GRAVITY * head_diff)
        return flow


class SluiceGate(BaseGate):
    """
    Represents a vertical slab gate (Sluice Gate).
    """

    def update_state(self, simulation_time: float, upstream_head: float, downstream_head: float) -> None:
        """
        Updates the flow rate based on head difference and gate opening.
        """
        super().update_state(simulation_time)
        self._current_flow_rate = self._calculate_flow(upstream_head, downstream_head)


class RadialGate(BaseGate):
    """
    Represents a radial or Tainter gate.
    """

    def update_state(self, simulation_time: float, upstream_head: float, downstream_head: float) -> None:
        """
        Updates the flow rate based on head difference and gate opening.
        """
        super().update_state(simulation_time)
        self._current_flow_rate = self._calculate_flow(upstream_head, downstream_head)


# --- Pump Models ---

class BasePump(ControllableStructure):
    """
    Abstract base class for all types of pumps.
    """

    def __init__(self, name: str, max_flow_rate: float, max_head: float, actuator_fault: Optional['ActuatorFault'] = None):
        super().__init__(name)
        self.max_flow_rate = max_flow_rate
        self.max_head = max_head
        self._is_on: bool = False
        self._power_consumption: float = 0.0
        self.actuator_fault = actuator_fault

    @property
    def is_on(self) -> bool:
        """Check if the pump is currently running."""
        return self._is_on

    @property
    def commanded_state(self) -> bool:
        """Returns the current operational state (True for On, False for Off)."""
        return self._is_on

    @commanded_state.setter
    def commanded_state(self, turn_on: bool) -> None:
        """
        Set the pump's operational state (True for On, False for Off),
        subject to actuator faults. A fault may force it on (1) or off (0).
        """
        commanded_numeric = 1.0 if turn_on else 0.0
        if self.actuator_fault:
            actual_numeric = self.actuator_fault.apply(commanded_numeric, self.simulation_time)
            self._is_on = (actual_numeric == 1.0)
        else:
            self._is_on = turn_on

        if not self._is_on:
            self._current_flow_rate = 0.0
            self._power_consumption = 0.0

    @property
    def power_consumption(self) -> float:
        """Get the current power consumption in Watts."""
        return self._power_consumption

    @abstractmethod
    def _calculate_performance(self, head: float) -> (float, float):
        """Calculates flow and power based on a characteristic curve."""
        pass


class CentrifugalPump(BasePump):
    """
    Represents a centrifugal pump with a simplified quadratic performance curve.
    """

    def update_state(self, simulation_time: float, head: float) -> None:
        """
        Updates flow rate and power consumption based on the operating head.
        """
        super().update_state(simulation_time)
        if not self.is_on or head > self.max_head:
            self._is_on = False # Turn off if head is too high
            self._current_flow_rate = 0.0
            self._power_consumption = 0.0
            return

        flow, power = self._calculate_performance(head)
        self._current_flow_rate = flow
        self._power_consumption = power

    def _calculate_performance(self, head: float) -> (float, float):
        """
        Calculates flow and power.
        """
        flow = self.max_flow_rate * np.sqrt(max(0, 1 - (head / self.max_head)**2))

        flow_ratio = (flow / self.max_flow_rate) if self.max_flow_rate > 0 else 0
        efficiency = 0.85 * np.sin(flow_ratio * np.pi / 1.4)
        efficiency = max(0.1, efficiency)

        power = (WATER_DENSITY * GRAVITY * flow * head) / efficiency
        return flow, power


class AxialFlowPump(CentrifugalPump):
    """
    Represents an axial flow pump.
    """
    pass


# --- Turbine Models ---

class BaseTurbine(ControllableStructure):
    """
    Abstract base class for all types of hydraulic turbines.
    """

    def __init__(self, name: str, max_flow_rate: float, actuator_fault: Optional['ActuatorFault'] = None):
        super().__init__(name)
        self.max_flow_rate = max_flow_rate
        self._power_generation: float = 0.0
        self._guide_vane_opening: float = 0.0 # Percentage
        self.actuator_fault = actuator_fault

    @property
    def guide_vane_opening(self) -> float:
        """Get the guide vane opening percentage (0-100)."""
        return self._guide_vane_opening

    @guide_vane_opening.setter
    def guide_vane_opening(self, value: float):
        """Set the guide vane opening, subject to actuator faults."""
        commanded_value = max(0.0, min(100.0, value))
        if self.actuator_fault:
            self._guide_vane_opening = self.actuator_fault.apply(commanded_value, self.simulation_time)
        else:
            self._guide_vane_opening = commanded_value

    @property
    def power_generation(self) -> float:
        """Get the current power generation in Watts."""
        return self._power_generation


class FrancisTurbine(BaseTurbine):
    """
    Represents a Francis (mixed-flow) turbine.
    """

    def update_state(self, simulation_time: float, head: float) -> None:
        """
        Updates flow rate and power generation based on head and vane opening.
        """
        super().update_state(simulation_time)
        if self.guide_vane_opening <= 0 or head <= 0:
            self._current_flow_rate = 0.0
            self._power_generation = 0.0
            return

        # Assuming nominal head of 50m for flow calculation
        flow_factor = np.sqrt(max(0, head / 50.0))
        self._current_flow_rate = self.max_flow_rate * (self.guide_vane_opening / 100.0) * flow_factor
        self._current_flow_rate = min(self._current_flow_rate, self.max_flow_rate)

        flow_ratio = (self._current_flow_rate / self.max_flow_rate) if self.max_flow_rate > 0 else 0
        efficiency = 0.92 * np.sin(flow_ratio * np.pi)
        efficiency = max(0.1, efficiency)

        self._power_generation = efficiency * WATER_DENSITY * GRAVITY * self._current_flow_rate * head


class KaplanTurbine(FrancisTurbine):
    """
    Represents a Kaplan (axial-flow) turbine.
    """
    pass


# --- Composite Station Models ---

class SluiceStation:
    """
    Manages a collection of sluice gates as a single unit.
    """

    def __init__(self, name: str, gates: List[BaseGate]):
        self.name = name
        self.gates = gates

    @property
    def total_flow_rate(self) -> float:
        """Get the combined flow rate from all gates in the station."""
        return sum(gate.current_flow_rate for gate in self.gates)

    def update_state(self, simulation_time: float, upstream_head: float, downstream_head: float) -> None:
        """
        Update the state of all gates in the station.
        """
        for gate in self.gates:
            gate.update_state(simulation_time, upstream_head, downstream_head)


class PumpingStation:
    """
    Manages a collection of pumps as a single unit.
    """

    def __init__(self, name: str, pumps: List[BasePump]):
        self.name = name
        self.pumps = pumps

    @property
    def total_flow_rate(self) -> float:
        """Get the combined flow rate from all active pumps in the station."""
        return sum(pump.current_flow_rate for pump in self.pumps)

    @property
    def total_power_consumption(self) -> float:
        """Get the combined power consumption of all pumps in the station."""
        return sum(pump.power_consumption for pump in self.pumps)

    def update_state(self, simulation_time: float, head: float) -> None:
        """
        Update the state of all pumps in the station.
        """
        for pump in self.pumps:
            # The pump's commanded_state is set externally by a controller.
            # This update call is for calculating the hydraulic results.
            pump.update_state(simulation_time, head)


class HydropowerStation:
    """
    A complex composite model representing a hydropower station.
    """

    def __init__(self,
                 name: str,
                 turbines: List[BaseTurbine],
                 spillway_gates: List[BaseGate],
                 other_outlets: List[BaseGate]):
        self.name = name
        self.turbines = turbines
        self.spillway_gates = spillway_gates
        self.other_outlets = other_outlets

    @property
    def total_power_generation(self) -> float:
        """Get the total power generated by all turbines."""
        return sum(turbine.power_generation for turbine in self.turbines)

    @property
    def turbine_flow_rate(self) -> float:
        """Get the total flow rate through all turbines."""
        return sum(turbine.current_flow_rate for turbine in self.turbines)

    @property
    def spillway_flow_rate(self) -> float:
        """Get the total flow rate through all spillway gates."""
        return sum(gate.current_flow_rate for gate in self.spillway_gates)

    @property
    def outlets_flow_rate(self) -> float:
        """Get the total flow rate through all other outlets."""
        return sum(outlet.current_flow_rate for outlet in self.other_outlets)

    @property
    def total_outflow(self) -> float:
        """Get the total outflow from the station."""
        return self.turbine_flow_rate + self.spillway_flow_rate + self.outlets_flow_rate

    def update_state(self, simulation_time: float, reservoir_head: float, tailwater_head: float) -> None:
        """
        Update the state of all components in the hydropower station.
        """
        turbine_head = reservoir_head - tailwater_head

        for turbine in self.turbines:
            turbine.update_state(simulation_time, head=turbine_head)

        for gate in self.spillway_gates:
            gate.update_state(simulation_time, upstream_head=reservoir_head, downstream_head=tailwater_head)

        for outlet in self.other_outlets:
            outlet.update_state(simulation_time, upstream_head=reservoir_head, downstream_head=tailwater_head)
