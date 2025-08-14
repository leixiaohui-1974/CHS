import collections
from dataclasses import dataclass
from ..modeling.base_model import BaseModel
from ..core.datastructures import State, Input


@dataclass
class IntegralPlusDelayState(State):
    output: float


@dataclass
class IntegralPlusDelayInput(Input):
    inflow: float


class IntegralPlusDelayModel(BaseModel):
    """
    A first-order inertial model with a time delay.
    This model represents a system where the rate of change of the output
    is proportional to the delayed input.
    Equation: dy/dt = K * u(t-T)
    """

    def __init__(self, K: float, T: float, dt: float, initial_value: float = 0.0, **kwargs):
        """
        Initializes the integral-plus-delay model.

        Args:
            K (float): The integral gain.
            T (float): The total delay time (transport delay).
            dt (float): The simulation time step.
            initial_value (float): The initial value of the input and output.
        """
        super().__init__()
        if dt <= 0:
            raise ValueError("dt must be positive.")
        if T < 0:
            raise ValueError("Time delay T cannot be negative.")

        self.K = K
        self.T = T
        self.dt = dt

        # Calculate the number of time steps for the delay
        self.delay_steps = int(round(T / dt))

        # Use a deque as a simple and efficient FIFO buffer for the input signal
        self.input_buffer: collections.deque = collections.deque([initial_value] * self.delay_steps, maxlen=self.delay_steps)

        self.input: IntegralPlusDelayInput = IntegralPlusDelayInput(inflow=initial_value)
        # The state holds the integrated output value
        self.state: IntegralPlusDelayState = IntegralPlusDelayState(output=initial_value)
        self.output = self.state.output

    def step(self, **kwargs):
        """
        Processes one time step of the model.
        """
        # Get the delayed input by taking the oldest value from the buffer
        if self.delay_steps > 0:
            delayed_input = self.input_buffer.popleft()
        else:
            delayed_input = self.input.inflow

        # Add the current input to the end of the buffer
        if self.delay_steps > 0:
            self.input_buffer.append(self.input.inflow)

        # Integrate using the delayed input
        # y(t) = y(t-dt) + K * u(t-T) * dt
        new_output = self.state.output + self.K * delayed_input * self.dt

        self.state.output = new_output
        self.output = new_output

    def get_state(self):
        """Returns the current state of the component."""
        return {
            "output": self.state.output,
            "buffer": list(self.input_buffer)
        }
