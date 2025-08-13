import numpy as np
from ..modeling.base_model import BaseModel
from ..core.datastructures import State, Input

class TimeSeriesDisturbance(BaseModel):
    """
    A component for generating disturbance signals from a predefined timeseries.
    """
    def __init__(self, times: list, values: list):
        """
        Initializes the disturbance generator.

        Args:
            times (list): A list of timestamps.
            values (list): A list of corresponding values.
        """
        super().__init__()
        if len(times) != len(values):
            raise ValueError("Length of 'times' and 'values' must be equal.")

        self.params = State(times=np.array(times), values=np.array(values))
        self.output = 0.0
        if self.params.times.size > 0:
            self.output = self.params.values[0]

    def step(self, dt: float, t: float):
        """
        Updates the output based on the current time and the timeseries data.
        It uses linear interpolation for times between defined points.
        """
        self.output = np.interp(t, self.params.times, self.params.values)

    def get_state(self):
        return {'output': self.output}
