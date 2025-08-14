from abc import abstractmethod
import numpy as np
from water_system_simulator.modeling.base_model import BaseModel
from water_system_simulator.data_processing.pipeline import DataProcessingPipeline

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
    A sensor that measures water level. It can add simple noise and/or use a
    more complex DataProcessingPipeline to simulate real-world sensor
    characteristics.
    """
    def __init__(self, pipeline: DataProcessingPipeline = None, noise_std_dev: float = 0.0, **kwargs):
        super().__init__(**kwargs)
        self.data_pipeline = pipeline
        self.noise_std_dev = noise_std_dev

    def measure(self, true_value: float) -> float:
        """
        Measures the true value, adds noise if configured, and then processes
        it through the data pipeline if one is provided.
        """
        # 1. Add simple noise if configured
        measured_value = true_value + np.random.normal(0, self.noise_std_dev)

        # 2. Process through the pipeline if it exists
        if self.data_pipeline:
            # The pipeline expects a dictionary.
            processed_data = self.data_pipeline.process({'value': measured_value})
            # The pipeline returns a dictionary. We expect a key 'value'.
            measured_value = processed_data.get('value', measured_value)

        return measured_value


class GateActuator(BaseActuator):
    """
    A model for a gate actuator that simulates response delay and travel time.
    The position is represented as a value from 0.0 (closed) to 1.0 (open).
    """
    def __init__(self,
                 travel_time: float = 120.0,
                 response_delay: float = 0.0,
                 initial_position: float = 0.0,
                 **kwargs):
        """
        Args:
            travel_time (float): Time in seconds to go from fully closed (0) to fully open (1).
            response_delay (float): Time in seconds to wait before starting to move after a command.
            initial_position (float): The starting position of the actuator.
        """
        super().__init__(initial_position=initial_position, **kwargs)
        if travel_time <= 0:
            raise ValueError("travel_time must be positive.")
        if response_delay < 0:
            raise ValueError("response_delay cannot be negative.")

        self.travel_time = travel_time
        self.response_delay = response_delay

        # State for handling response delay
        self.target_command = self.current_position
        self.time_since_command_change = self.response_delay # Start as if delay is over

    def step(self, command: float, dt: float):
        """
        Moves the gate towards the command position, respecting delay and travel time.

        Args:
            command (float): The target position for the gate (0.0 to 1.0).
            dt (float): The simulation time step in seconds.
        """
        clipped_command = np.clip(command, 0.0, 1.0)

        # Check if the command has changed
        if clipped_command != self.target_command:
            self.target_command = clipped_command
            self.time_since_command_change = 0.0

        # Increment time since command change, but don't let it grow indefinitely
        if self.time_since_command_change < self.response_delay:
            self.time_since_command_change += dt

        # Only move if the response delay has passed
        if self.time_since_command_change < self.response_delay:
            # Still in delay period, do nothing
            self.output = self.current_position
            return self.current_position

        # --- Movement logic (same as before, but uses self.target_command) ---
        max_speed = 1.0 / self.travel_time
        max_change = max_speed * dt
        difference = self.target_command - self.current_position

        if abs(difference) <= max_change:
            self.current_position = self.target_command
        else:
            self.current_position += np.sign(difference) * max_change

        self.current_position = np.clip(self.current_position, 0.0, 1.0)
        self.output = self.current_position
        return self.current_position
