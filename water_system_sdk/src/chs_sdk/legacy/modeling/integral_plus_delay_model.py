import collections
from dataclasses import dataclass, field
from ..modeling.base_model import BaseModel
from ..core.datastructures import State, Input


@dataclass
class IntegralPlusDelayState(State):
    output: float


@dataclass
class IntegralPlusDelayInput(Input):
    """Input structure for the model, separating base inflow from control action."""
    inflow: float = 0.0
    control_inflow: float = 0.0


class IntegralPlusDelayModel(BaseModel):
    """
    A first-order inertial model with a time delay.
    This model represents a system where the rate of change of the output
    is proportional to the delayed total input.
    Equation: dy/dt = K * u_total(t-T)
    where u_total = inflow + control_inflow
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

        self.delay_steps = int(round(T / dt))
        # Initial total inflow is based on the initial_value passed
        self.input_buffer: collections.deque = collections.deque([initial_value] * self.delay_steps, maxlen=self.delay_steps)

        self.input: IntegralPlusDelayInput = IntegralPlusDelayInput()
        self.state: IntegralPlusDelayState = IntegralPlusDelayState(output=initial_value)
        self.output = self.state.output

    def step(self, **kwargs):
        """
        Processes one time step of the model.
        """
        total_inflow = self.input.inflow + self.input.control_inflow

        if self.delay_steps > 0:
            delayed_input = self.input_buffer.popleft()
            self.input_buffer.append(total_inflow)
        else:
            delayed_input = total_inflow

        new_output = self.state.output + self.K * delayed_input * self.dt

        self.state.output = new_output
        self.output = new_output

    def get_state(self):
        """Returns the current state of the component."""
        return {
            "output": self.state.output,
            "buffer": list(self.input_buffer)
        }
