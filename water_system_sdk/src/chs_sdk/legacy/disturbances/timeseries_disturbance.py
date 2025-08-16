import numpy as np
from typing import List, Any, Dict
from dataclasses import dataclass, asdict
from ..modeling.base_model import BaseModel
from ..core.datastructures import State, Input

@dataclass
class TimeseriesState(State):
    output: float

@dataclass
class TimeseriesParams(Input):
    times: np.ndarray
    values: np.ndarray

class TimeSeriesDisturbance(BaseModel):
    """
    A component for generating disturbance signals from a predefined timeseries.
    """
    def __init__(self, times: List[float], values: List[float], **kwargs: Any) -> None:
        """
        Initializes the disturbance generator.

        Args:
            times: A list of timestamps.
            values: A list of corresponding values.
        """
        super().__init__(**kwargs)
        if len(times) != len(values):
            raise ValueError("Length of 'times' and 'values' must be equal.")

        self.params: TimeseriesParams = TimeseriesParams(times=np.array(times), values=np.array(values))
        initial_output = 0.0
        if self.params.times.size > 0:
            initial_output = self.params.values[0]

        self.state: TimeseriesState = TimeseriesState(output=initial_output)
        self.output: float = initial_output

    def step(self, dt: float, t: float, **kwargs: Any) -> None:
        """
        Updates the output based on the current time and the timeseries data.
        It uses linear interpolation for times between defined points.
        """
        self.state.output = float(np.interp(t, self.params.times, self.params.values))
        self.output = self.state.output

    def get_state(self) -> Dict[str, Any]:
        return asdict(self.state)
