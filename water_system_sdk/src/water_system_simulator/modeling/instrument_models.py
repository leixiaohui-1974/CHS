from abc import ABC, abstractmethod
import numpy as np
from .base_model import BaseModel

class BaseSensor(BaseModel, ABC):
    """
    Abstract base class for all sensor models.
    A sensor measures a true value from the system and produces a measurement.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.measured_value = None

    @abstractmethod
    def measure(self, true_value: float):
        """
        Takes a true value from the system and updates the sensor's
        internal state (e.g., its measured_value).
        """
        pass

class BaseActuator(BaseModel, ABC):
    """
    Abstract base class for all actuator models.
    An actuator takes a command and translates it into a physical change.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_position = 0.0

    @abstractmethod
    def step(self, command: float, dt: float):
        """
        Updates the actuator's internal state based on a command over a
        time step dt. Note the different signature from BaseModel.step.
        """
        pass

class LevelSensor(BaseSensor):
    """
    A sensor that measures water level with Gaussian noise.
    """
    def __init__(self, noise_std_dev: float = 0.05, **kwargs):
        super().__init__(**kwargs)
        self.noise_std_dev = noise_std_dev
        # Initialize measured_value
        self.measured_value = 0.0

    def measure(self, true_value: float):
        """
        Adds Gaussian noise to the true water level.
        The result is stored in the `measured_value` attribute.
        """
        noise = np.random.normal(0, self.noise_std_dev)
        self.measured_value = true_value + noise
        # For consistency, also update the 'output' attribute from BaseModel
        self.output = self.measured_value
        return self.measured_value

class GateActuator(BaseActuator):
    """
    An actuator that simulates the movement of a gate, considering its travel time.
    The gate position is represented as a value from 0.0 (fully closed) to 1.0 (fully open).
    """
    def __init__(self, travel_time: float = 120.0, initial_position: float = 0.0, **kwargs):
        super().__init__(**kwargs)
        if travel_time <= 0:
            raise ValueError("travel_time must be positive.")
        self.travel_time = travel_time # Time for full travel (e.g., 0 to 1)
        self.current_position = initial_position # Initial position of the gate
        # For consistency, also update the 'output' attribute from BaseModel
        self.output = self.current_position

    def step(self, command: float, dt: float):
        """
        Moves the gate towards the command position based on travel_time.

        Args:
            command: The target position for the gate (0.0 to 1.0).
            dt: The simulation time step in seconds.
        """
        # Sanitize the command to be within [0, 1]
        target_position = np.clip(command, 0.0, 1.0)

        # Maximum change in position per second
        max_speed = 1.0 / self.travel_time

        # Maximum change for this time step
        max_change = max_speed * dt

        # Required change to reach the target
        required_change = target_position - self.current_position

        # Actual change is limited by max_change
        if abs(required_change) > max_change:
            actual_change = max_change * np.sign(required_change)
        else:
            actual_change = required_change

        # Update the position and ensure it stays within the [0, 1] bounds
        self.current_position = np.clip(self.current_position + actual_change, 0.0, 1.0)

        # For consistency, also update the 'output' attribute from BaseModel
        self.output = self.current_position
        return self.current_position
