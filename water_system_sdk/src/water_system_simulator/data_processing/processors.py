import numpy as np
from collections import deque
from .base_processor import BaseDataProcessor

class OutlierRemover(BaseDataProcessor):
    """
    Removes outliers by clipping values outside a defined range.
    """
    def __init__(self, min_val: float, max_val: float):
        self.min_val = min_val
        self.max_val = max_val

    def process(self, data_input: dict) -> dict:
        processed_data = {}
        for key, value in data_input.items():
            processed_data[key] = np.clip(value, self.min_val, self.max_val)
        return processed_data

class DataSmoother(BaseDataProcessor):
    """
    Smooths data using a simple moving average filter.
    """
    def __init__(self, window_size: int = 5):
        if window_size < 1:
            raise ValueError("Window size must be a positive integer.")
        self.window_size = window_size
        self.history = {}  # key -> deque of previous values

    def process(self, data_input: dict) -> dict:
        processed_data = {}
        for key, value in data_input.items():
            if key not in self.history:
                self.history[key] = deque(maxlen=self.window_size)

            self.history[key].append(value)
            processed_data[key] = np.mean(self.history[key])

        return processed_data

class DataFusionEngine(BaseDataProcessor):
    """
    Fuses data from multiple sources using a specified mode.
    """
    def __init__(self, mode: str, **kwargs):
        self.mode = mode
        if self.mode == 'weighted_average':
            self.weights = kwargs.get('weights', {})
            if not self.weights:
                raise ValueError("Weighted average mode requires a 'weights' dictionary.")
        elif self.mode == 'kalman_filter':
            # State: [value, uncertainty]
            self.x = kwargs.get('initial_estimate', 0.0)  # Initial state estimate
            self.P = kwargs.get('initial_uncertainty', 1.0) # Initial estimate uncertainty
            self.Q = kwargs.get('process_noise', 1e-5) # Process noise covariance
            self.R = kwargs.get('measurement_noise', 0.1**2) # Measurement noise covariance
        else:
            raise ValueError(f"Unknown fusion mode: {self.mode}")

    def process(self, data_input: dict) -> dict:
        if self.mode == 'weighted_average':
            return self._process_weighted_average(data_input)
        elif self.mode == 'kalman_filter':
            return self._process_kalman_filter(data_input)
        return {}

    def _process_weighted_average(self, data_input: dict) -> dict:
        numerator = 0.0
        denominator = 0.0
        for key, value in data_input.items():
            weight = self.weights.get(key)
            if weight is None:
                continue # Or raise an error, for now we just skip
            numerator += value * weight
            denominator += weight

        fused_value = numerator / denominator if denominator != 0 else 0
        return {'fused_value': fused_value}

    def _process_kalman_filter(self, data_input: dict) -> dict:
        # 1. Prediction Step
        # In our simple 1D case, we assume the state doesn't change on its own.
        # x_hat = 1 * x
        # P = 1 * P * 1^T + Q
        self.P = self.P + self.Q

        # 2. Update Step (for each measurement)
        # We treat each entry in data_input as a separate measurement of the same state.
        for key, z in data_input.items():
            # In our simple 1D case, H=1
            K = self.P / (self.P + self.R) # Kalman Gain
            self.x = self.x + K * (z - self.x) # Update estimate
            self.P = (1 - K) * self.P # Update uncertainty

        return {'fused_value': self.x}

class NoiseInjector(BaseDataProcessor):
    """
    Injects Gaussian noise into the data.
    """
    def __init__(self, noise_std_dev: float):
        self.noise_std_dev = noise_std_dev

    def process(self, data_input: dict) -> dict:
        processed_data = {}
        for key, value in data_input.items():
            noise = np.random.normal(0, self.noise_std_dev)
            processed_data[key] = value + noise
        return processed_data
