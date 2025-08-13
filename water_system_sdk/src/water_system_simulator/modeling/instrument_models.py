from abc import abstractmethod
import numpy as np
from water_system_simulator.modeling.base_model import BaseModel

# Phase 1: Instrument Layer
# Action 1: Create new base classes (Corrected Implementation)

class BaseSensor(BaseModel):
    """
    Abstract base class for all sensor models.
    A sensor measures a true value from the system.
    It implements the 'step' method by wrapping a 'measure' method.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.measured_value = 0.0
        self.output = 0.0 # Ensure output is initialized

    @abstractmethod
    def measure(self, true_value: float) -> float:
        """
        Takes a true value and produces a measured value.
        This is the core logic to be implemented by concrete sensors.
        """
        pass

    def step(self, true_value: float):
        """
        Standard step method for SimulationManager. It wraps the measure method.
        The 'true_value' is passed in via the execution_order config.
        """
        self.measured_value = self.measure(true_value)
        self.output = self.measured_value

    def get_state(self):
        """
        Returns the current state of the sensor.
        """
        return {"measured_value": self.measured_value, "output": self.output}


class BaseActuator(BaseModel):
    """
    Abstract base class for all actuator models.
    An actuator takes a command and acts upon the system.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_position = kwargs.get('initial_position', 0.0)
        self.output = self.current_position # Ensure output is initialized

    @abstractmethod
    def step(self, command: float, dt: float):
        """
        Executes a command over a time step dt.
        This is the core logic to be implemented by concrete actuators.
        Note: The signature differs from the simple BaseModel.step(), but is
        compatible with the `step(*args, **kwargs)` definition and is called
        via the expressive execution_order config.
        """
        pass

    def get_state(self):
        """
        Returns the current state of the actuator.
        """
        return {"current_position": self.current_position, "output": self.output}


# Action 2: Develop concrete instrument models

class LevelSensor(BaseSensor):
    """
    A sensor that measures water level with Gaussian noise.
    """
    def __init__(self, noise_std_dev: float = 0.05, **kwargs):
        super().__init__(**kwargs)
        self.noise_std_dev = noise_std_dev

    def measure(self, true_value: float) -> float:
        """
        Adds Gaussian noise to the true water level.
        """
        noise = np.random.normal(0, self.noise_std_dev)
        measured_value = true_value + noise
        return measured_value


class GateActuator(BaseActuator):
    """
    A model for a gate actuator that has a finite travel time.
    The position is represented as a value from 0.0 (closed) to 1.0 (open).
    """
    def __init__(self, travel_time: float = 120.0, **kwargs):
        """
        Args:
            travel_time: Time in seconds to go from fully closed (0) to fully open (1).
        """
        super().__init__(**kwargs)
        if travel_time <= 0:
            raise ValueError("travel_time must be positive.")
        self.travel_time = travel_time

    def step(self, command: float, dt: float):
        """
        Moves the gate towards the command position based on travel_time.

        Args:
            command: The target position for the gate (0.0 to 1.0).
            dt: The simulation time step in seconds.
        """
        target_position = np.clip(command, 0.0, 1.0)
        max_speed = 1.0 / self.travel_time
        max_change = max_speed * dt
        difference = target_position - self.current_position

        if abs(difference) <= max_change:
            self.current_position = target_position
        else:
            self.current_position += np.sign(difference) * max_change

        self.current_position = np.clip(self.current_position, 0.0, 1.0)
        self.output = self.current_position
        return self.current_position
