"""
Models for external disturbances and internal system faults.

This module provides classes to simulate a variety of events that can affect
a water management system's state or behavior. These are divided into:
- Disturbances: Events that directly alter system state (e.g., inflows/outflows).
- Faults: Events that alter the behavior of system components (e.g., sensors).
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import List, Union, Dict, Any, Optional, Tuple

# --- Disturbance Models ---

class BaseDisturbance(ABC):
    """
    Abstract base class for any disturbance affecting the system.

    A disturbance is an external event that adds or removes water from a
    node in the system (e.g., a reservoir or river reach).
    """

    @abstractmethod
    def get_value(self, simulation_time: float) -> float:
        """
        Calculates the disturbance value at a given simulation time.

        Args:
            simulation_time (float): The current time in the simulation (e.g., in hours).

        Returns:
            float: The magnitude of the disturbance (e.g., in m^3/s).
        """
        pass


class RainfallRunoff(BaseDisturbance):
    """
    Simulates runoff from a rainfall event based on a time series.

    The runoff is determined by interpolating a given time series of
    rainfall intensity and applying a runoff coefficient.
    """

    def __init__(self, catchment_area: float, runoff_coefficient: float, time_series: Dict[float, float]):
        """
        Args:
            catchment_area (float): The area of the catchment in square meters.
            runoff_coefficient (float): A dimensionless factor (0-1) representing the
                                        fraction of rainfall that becomes runoff.
            time_series (Dict[float, float]): A dictionary mapping simulation time (hours)
                                              to rainfall intensity (mm/hr).
        """
        self.catchment_area = catchment_area
        self.runoff_coefficient = runoff_coefficient
        self._times = sorted(time_series.keys())
        self._intensities = [time_series[t] for t in self._times]

    def get_value(self, simulation_time: float) -> float:
        """
        Calculates runoff in m^3/s at the given simulation time.
        """
        # Interpolate rainfall intensity (mm/hr)
        intensity_mm_hr = np.interp(simulation_time, self._times, self._intensities)

        # Convert intensity from mm/hr to m/s
        intensity_m_s = intensity_mm_hr / (1000 * 3600)

        # Calculate runoff in m^3/s
        runoff = intensity_m_s * self.catchment_area * self.runoff_coefficient
        return runoff


class DemandProfile(BaseDisturbance):
    """
    Simulates water demand based on a predefined time-based profile.
    """

    def __init__(self, time_series: Dict[float, float]):
        """
        Args:
            time_series (Dict[float, float]): A dictionary mapping simulation time (hours)
                                              to water demand (m^3/s).
        """
        self._times = sorted(time_series.keys())
        self._demands = [time_series[t] for t in self._times]

    def get_value(self, simulation_time: float) -> float:
        """
        Returns the water demand in m^3/s by interpolating the profile.
        """
        demand = np.interp(simulation_time, self._times, self._demands)
        return -abs(demand) # Demand is a water loss


class SuddenStorm(BaseDisturbance):
    """
    Simulates a sudden, intense, and typically short-lived storm event.
    """

    def __init__(self, start_time: float, duration: float, intensity: float):
        """
        Args:
            start_time (float): The simulation time when the storm begins (hours).
            duration (float): The duration of the storm (hours).
            intensity (float): The constant inflow rate during the storm (m^3/s).
        """
        self.start_time = start_time
        self.end_time = start_time + duration
        self.intensity = intensity

    def get_value(self, simulation_time: float) -> float:
        """
        Returns the storm inflow if within the event window, otherwise zero.
        """
        if self.start_time <= simulation_time < self.end_time:
            return self.intensity
        return 0.0


class Evaporation(BaseDisturbance):
    """
    Simulates water loss due to evaporation.
    """

    def __init__(self, surface_area_m2: float, evaporation_rate_mm_per_day: float):
        """
        Args:
            surface_area_m2 (float): The water surface area in square meters.
            evaporation_rate_mm_per_day (float): The rate of evaporation.
        """
        self.surface_area_m2 = surface_area_m2
        # Convert mm/day to m/s
        self.evaporation_rate_m_s = evaporation_rate_mm_per_day / (1000 * 24 * 3600)

    def get_value(self, simulation_time: float) -> float:
        """
        Returns the constant evaporation loss in m^3/s.
        A more complex model could vary the rate with temperature.
        """
        loss = self.surface_area_m2 * self.evaporation_rate_m_s
        return -abs(loss)


class Seepage(BaseDisturbance):
    """
    Simulates continuous water loss due to seepage.
    """

    def __init__(self, base_seepage_rate_m3_s: float):
        """
        Args:
            base_seepage_rate_m3_s (float): The base rate of seepage loss.
        """
        self.base_seepage_rate_m3_s = base_seepage_rate_m3_s

    def get_value(self, simulation_time: float) -> float:
        """
        Returns the seepage loss. A more complex model could make this
        dependent on the water level (head).
        """
        return -abs(self.base_seepage_rate_m3_s)


class UnaccountedFlow(BaseDisturbance):
    """
    Simulates random, unaccounted for inflows or outflows using a normal distribution.
    """

    def __init__(self, mean_flow: float, std_dev: float):
        """
        Args:
            mean_flow (float): The mean of the random flow (m^3/s).
            std_dev (float): The standard deviation of the random flow (m^3/s).
        """
        self.mean_flow = mean_flow
        self.std_dev = std_dev

    def get_value(self, simulation_time: float) -> float:
        """
        Returns a new random flow value at each call.
        """
        return np.random.normal(self.mean_flow, self.std_dev)


# --- Fault Models ---

class BaseFault(ABC):
    """
    Abstract base class for any fault affecting a system component.
    """
    def __init__(self, start_time: float, end_time: float = float('inf')):
        self.start_time = start_time
        self.end_time = end_time

    def is_active(self, simulation_time: float) -> bool:
        """Checks if the fault is active at the given simulation time."""
        return self.start_time <= simulation_time < self.end_time

    @abstractmethod
    def apply(self, *args, **kwargs) -> Any:
        """Apply the fault to a value or component."""
        pass


class SensorFault(BaseFault):
    """
    Simulates a sensor fault with various modes.
    """
    def __init__(self, start_time: float, end_time: float, mode: str, **kwargs):
        """
        Args:
            start_time (float): Fault start time.
            end_time (float): Fault end time.
            mode (str): Fault mode: 'stuck', 'noise', 'drift', 'outage'.
            **kwargs: Parameters for the fault mode.
                stuck: 'value' (the value it's stuck at)
                noise: 'std_dev' (standard deviation of noise)
                drift: 'rate' (drift rate per hour)
        """
        super().__init__(start_time, end_time)
        if mode not in ['stuck', 'noise', 'drift', 'outage']:
            raise ValueError(f"Unknown fault mode: {mode}")
        self.mode = mode
        self.params = kwargs
        self._initial_drift_value = None

    def apply(self, true_value: float, simulation_time: float) -> Optional[float]:
        """
        Applies the fault to a true sensor value.

        Args:
            true_value (float): The actual, correct value.
            simulation_time (float): The current simulation time.

        Returns:
            The faulted sensor value, or None for an outage.
        """
        if not self.is_active(simulation_time):
            return true_value

        if self.mode == 'stuck':
            return self.params.get('value', true_value)
        elif self.mode == 'noise':
            noise = np.random.normal(0, self.params.get('std_dev', 0))
            return true_value + noise
        elif self.mode == 'drift':
            if self._initial_drift_value is None:
                self._initial_drift_value = true_value
            time_in_fault = simulation_time - self.start_time
            drift_amount = time_in_fault * self.params.get('rate', 0)
            return self._initial_drift_value + drift_amount
        elif self.mode == 'outage':
            return None
        return true_value


class ActuatorFault(BaseFault):
    """
    Simulates an actuator fault (e.g., a stuck gate).
    """
    def __init__(self, start_time: float, end_time: float, stuck_position: float):
        super().__init__(start_time, end_time)
        self.stuck_position = stuck_position

    def apply(self, commanded_value: float, simulation_time: float) -> float:
        """
        Applies the fault to a commanded value. If active, returns the stuck
        position, otherwise returns the commanded value.
        """
        if self.is_active(simulation_time):
            return self.stuck_position
        return commanded_value


class CommunicationFault(BaseFault):
    """
    Simulates a communication link failure.

    A simulation engine can check `is_active` to determine if sensor values
    are received or commands can be sent.
    """
    def apply(self) -> None:
        """This fault doesn't modify a value, it prevents an action."""
        print(f"Communication fault active at time {self.start_time}")


class NodeUnavailable(BaseFault):
    """
    Simulates an entire control node (e.g., RTU) going offline.

    A simulation engine can check `is_active` to determine if any component
    connected to this node is available.
    """
    def apply(self) -> None:
        """This fault indicates a node is offline."""
        print(f"Node unavailable at time {self.start_time}")
