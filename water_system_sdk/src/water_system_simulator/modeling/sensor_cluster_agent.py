import numpy as np
from .base_model import BaseModel

class SensorClusterAgent(BaseModel):
    """
    Simulates a cluster of sensors measuring a physical value with noise and bias.
    """
    def __init__(self, num_sensors: int = 1, noise_std_dev: float = 0.5, bias: float = 0.0, **kwargs):
        """
        Initializes the SensorClusterAgent.

        Args:
            num_sensors (int): The number of sensors in the cluster.
            noise_std_dev (float): The standard deviation of the Gaussian noise.
            bias (float): A constant bias added to the measurements.
        """
        super().__init__(**kwargs)
        self.num_sensors = num_sensors
        self.noise_std_dev = noise_std_dev
        self.bias = bias
        self.state = {'readings': {f'sensor_{i+1}': 0.0 for i in range(num_sensors)}}
        self.output = self.state['readings'] # Expose top-level output

    def step(self, true_value: float, **kwargs):
        """
        Generates new sensor readings based on a true value.

        Args:
            true_value (float): The ground truth value to be measured.
        """
        for i in range(self.num_sensors):
            noise = np.random.normal(0, self.noise_std_dev)
            reading = true_value + self.bias + noise
            self.state['readings'][f'sensor_{i+1}'] = reading

        self.output = self.state['readings']
        return self.output

    def get_state(self) -> dict:
        """
        Returns the current state of the sensor readings.
        """
        return self.state
