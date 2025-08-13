# This file will contain the new generation of disturbance agents.
# These agents are active models that can evolve their own state over time.

from ..modeling.base_model import BaseModel
from abc import abstractmethod

class BaseDisturbanceAgent(BaseModel):
    """
    Abstract base class for all disturbance agent models.

    Disturbance agents are active components that can have their own internal
    state and logic, allowing for the simulation of complex, dynamic environmental
    conditions and faults.
    """
    def __init__(self, **kwargs):
        super().__init__()
        # The output of a disturbance agent is the disturbance value it injects.
        self.output = 0.0

    @abstractmethod
    def step(self, t, dt):
        """
        Represents a single time step of the agent's execution.

        This method must be implemented by all subclasses. It should
        update the internal state of the agent and set the `self.output` value.

        Args:
            t (float): The current simulation time.
            dt (float): The simulation time step.
        """
        pass

    @abstractmethod
    def get_state(self):
        """
        Returns a dictionary of the agent's current state.
        """
        pass

class RainfallAgent(BaseDisturbanceAgent):
    """
    A disturbance agent that simulates a rainfall event based on a predefined
    time series.
    """
    def __init__(self, rainfall_pattern: list, **kwargs):
        """
        Initializes the RainfallAgent.

        Args:
            rainfall_pattern (list): A time series of rainfall values.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self.rainfall_pattern = rainfall_pattern
        self.current_step = 0

    def step(self, t, dt):
        """
        Updates the agent's output to the rainfall value at the current time.
        """
        if self.current_step < len(self.rainfall_pattern):
            self.output = self.rainfall_pattern[self.current_step]
        else:
            self.output = 0.0  # No rainfall after the pattern ends

        # This simple model advances one step in the pattern per simulation step.
        # A more complex model could use 't' and 'dt' to interpolate.
        self.current_step += 1

    def get_state(self):
        """Returns the current state of the agent."""
        return {
            "type": "RainfallAgent",
            "current_step": self.current_step,
            "output": self.output
        }

class FaultAgent(BaseDisturbanceAgent):
    """
    A disturbance agent that simulates a sequence of faults or failures in
    the system. It can model complex, persistent faults.
    """
    def __init__(self, fault_sequence: list, **kwargs):
        """
        Initializes the FaultAgent.

        Args:
            fault_sequence (list): A list of fault event dictionaries.
                Each dictionary should contain:
                - 'type': The type of fault (e.g., 'SensorDrift', 'PipeLeakage').
                - 'start_time': The simulation time when the fault begins.
                - ... other fault-specific parameters.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self.fault_sequence = sorted(fault_sequence, key=lambda x: x['start_time'])
        self.active_faults = []
        self.output = 0.0 # Default output, can represent different things

    def step(self, t, dt):
        """
        Updates the agent's state based on the fault sequence.
        """
        # Check for new faults to activate
        for fault in self.fault_sequence:
            if fault not in self.active_faults and t >= fault['start_time']:
                self.active_faults.append(fault)

        # Apply the logic for active faults
        # For now, we just implement the logic for the first active fault.
        # A more advanced implementation could combine multiple faults.
        if not self.active_faults:
            self.output = 0.0
            return

        current_fault = self.active_faults[-1] # Use the most recent fault
        fault_type = current_fault.get('type')

        if fault_type == 'SensorDrift':
            self._apply_sensor_drift(current_fault, t)
        elif fault_type == 'ActuatorWear':
            self._apply_actuator_wear(current_fault, t)
        elif fault_type == 'PipeLeakage':
            self._apply_pipe_leakage(current_fault, t)
        else:
            self.output = 0.0

    def _apply_sensor_drift(self, fault, t):
        """Calculates the output for a sensor drift fault."""
        drift_rate = fault.get('drift_rate', 0.0) # drift per second
        start_time = fault.get('start_time', t)
        time_since_start = t - start_time
        self.output = time_since_start * drift_rate

    def _apply_actuator_wear(self, fault, t):
        """Calculates the output for an actuator wear fault."""
        wear_rate = fault.get('wear_rate', 0.0) # efficiency loss per second
        initial_efficiency = fault.get('initial_efficiency', 1.0)
        start_time = fault.get('start_time', t)
        time_since_start = t - start_time
        efficiency = initial_efficiency - (time_since_start * wear_rate)
        self.output = max(0, efficiency) # Efficiency cannot be negative

    def _apply_pipe_leakage(self, fault, t):
        """Calculates the output for a pipe leakage fault."""
        leakage_rate = fault.get('leakage_rate', 0.0) # leakage increase per second
        max_leakage = fault.get('max_leakage', 0.0)
        start_time = fault.get('start_time', t)
        time_since_start = t - start_time
        leakage = time_since_start * leakage_rate
        self.output = min(leakage, max_leakage)

    def get_state(self):
        """Returns the current state of the agent."""
        return {
            "type": "FaultAgent",
            "active_faults": self.active_faults,
            "output": self.output
        }

class PriceAgent(BaseDisturbanceAgent):
    """
    A disturbance agent that simulates the fluctuation of electricity prices
    based on a predefined time series (e.g., time-of-use pricing).
    """
    def __init__(self, price_pattern: list, **kwargs):
        """
        Initializes the PriceAgent.

        Args:
            price_pattern (list): A time series of price values.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self.price_pattern = price_pattern
        self.current_step = 0

    def step(self, t, dt):
        """
        Updates the agent's output to the price value at the current time.
        """
        if self.current_step < len(self.price_pattern):
            self.output = self.price_pattern[self.current_step]
        else:
            # If the pattern ends, assume the last price value continues.
            self.output = self.price_pattern[-1] if self.price_pattern else 0.0

        self.current_step += 1

    def get_state(self):
        """Returns the current state of the agent."""
        return {
            "type": "PriceAgent",
            "current_step": self.current_step,
            "output": self.output
        }

class DemandAgent(BaseDisturbanceAgent):
    """
    A disturbance agent that simulates water demand from consumers based on a
    predefined time series.
    """
    def __init__(self, demand_pattern: list, **kwargs):
        """
        Initializes the DemandAgent.

        Args:
            demand_pattern (list): A time series of water demand values.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)
        self.demand_pattern = demand_pattern
        self.current_step = 0

    def step(self, t, dt):
        """
        Updates the agent's output to the demand value at the current time.
        """
        if self.current_step < len(self.demand_pattern):
            self.output = self.demand_pattern[self.current_step]
        else:
            # If the pattern ends, assume the last demand value continues.
            self.output = self.demand_pattern[-1] if self.demand_pattern else 0.0

        self.current_step += 1

    def get_state(self):
        """Returns the current state of the agent."""
        return {
            "type": "DemandAgent",
            "current_step": self.current_step,
            "output": self.output
        }
