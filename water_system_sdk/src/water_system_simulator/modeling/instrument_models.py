from .base_model import BaseModel
import numpy as np

class SensorBase(BaseModel):
    """
    Base class for all sensor models, simulating real-world imperfections.
    """
    def __init__(self,
                 noise_stddev: float = 0.0,
                 bias: float = 0.0,
                 drift: float = 0.0,          # units per second
                 lag: float = 0.0,            # response time constant (s)
                 quantization_step: float = 0.0,
                 fault_mode: str = 'none',    # 'none', 'stuck', 'offset', 'disconnected'
                 fault_value: float = 0.0,
                 **kwargs):
        super().__init__(**kwargs)
        self.noise_stddev = noise_stddev
        self.bias = bias
        self.drift = drift
        self.lag = lag
        self.quantization_step = quantization_step
        self.fault_mode = fault_mode
        self.fault_value = fault_value
        self.current_drift = 0.0
        self.last_measurement = 0.0

    def measure(self, true_value: float, dt: float) -> float:
        """
        Takes a true value and returns a measured value, applying imperfections.

        Args:
            true_value (float): The actual, ground-truth value.
            dt (float): The simulation time step.

        Returns:
            float: The simulated measurement from the sensor.
        """
        # 1. Apply Fault Modes
        if self.fault_mode == 'stuck':
            return self.fault_value
        elif self.fault_mode == 'disconnected':
            return 0.0 # Or None, depending on system design
        elif self.fault_mode == 'offset':
            true_value += self.fault_value

        # 2. Apply Drift
        self.current_drift += self.drift * dt
        value_with_drift = true_value + self.current_drift

        # 3. Apply Bias
        value_with_bias = value_with_drift + self.bias

        # 4. Apply Sensor Lag (First-order system)
        if self.lag > 0:
            # y_k = alpha * x_k + (1 - alpha) * y_{k-1}
            # where alpha = dt / (lag + dt)
            alpha = dt / (self.lag + dt)
            lagged_value = alpha * value_with_bias + (1 - alpha) * self.last_measurement
            self.last_measurement = lagged_value
        else:
            lagged_value = value_with_bias
            self.last_measurement = lagged_value

        # 5. Apply Noise
        noisy_value = np.random.normal(loc=lagged_value, scale=self.noise_stddev)

        # 6. Apply Quantization
        if self.quantization_step > 0:
            quantized_value = np.round(noisy_value / self.quantization_step) * self.quantization_step
        else:
            quantized_value = noisy_value

        return quantized_value

    def set_fault_mode(self, mode: str, value: float = 0.0):
        """
        Sets a fault mode for the sensor.
        """
        self.fault_mode = mode
        self.fault_value = value
