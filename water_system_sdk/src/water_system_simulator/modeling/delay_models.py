import collections
from ..modeling.base_model import BaseModel
from ..core.datastructures import State, Input

class IntegralDelayModel(BaseModel):
    """
    A model that introduces a pure time delay to a signal.
    The delay is an integer number of time steps.
    """
    def __init__(self, delay: float, dt: float, initial_value: float = 0.0, **kwargs):
        """
        Initializes the integral delay model.

        Args:
            delay (float): The total delay time.
            dt (float): The simulation time step.
            initial_value (float): The initial value to output during the delay period.
        """
        super().__init__()
        if dt <= 0:
            raise ValueError("dt must be positive.")
        if delay < 0:
            raise ValueError("delay cannot be negative.")

        # Calculate the number of time steps for the delay
        self.delay_steps = int(round(delay / dt))

        # Use a deque as a simple and efficient FIFO buffer
        self.buffer = collections.deque([initial_value] * self.delay_steps, maxlen=self.delay_steps)

        self.input = Input(inflow=initial_value)
        self.state = State(output=initial_value)
        self.output = self.state.output

    def step(self, **kwargs):
        """
        Processes one time step of the delay.
        It takes the current input, adds it to the buffer, and outputs the
        value that has finished its delay period.
        """
        # The oldest value in the buffer is the output for this step
        # If buffer is empty (delay is 0), this should not happen with proper init.
        # But as a safeguard, we could return current input.
        if not self.buffer:
            output_value = self.input.inflow
        else:
            output_value = self.buffer.popleft()

        # Add the current input to the end of the buffer
        self.buffer.append(self.input.inflow)

        self.state.output = output_value
        self.output = output_value

    def get_state(self):
        """Returns the current state of the component."""
        # The 'state' of this model is its output and the internal buffer content
        return {
            "output": self.state.output,
            "buffer": list(self.buffer)
        }
