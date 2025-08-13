from ..modeling.base_model import BaseModel
from ..core.datastructures import State, Input

class Disturbance(BaseModel):
    """
    A component for generating predefined disturbance signals.
    """
    def __init__(self, signal_type: str, **kwargs):
        """
        Initializes the disturbance generator.

        Args:
            signal_type (str): Type of signal ('constant', 'step').
            **kwargs:
                For 'constant':
                    value (float): The constant output value.
                For 'step':
                    initial_value (float): Value before the step.
                    step_value (float): Value after the step.
                    step_time (float): Time at which the step occurs.
        """
        super().__init__()
        self.signal_type = signal_type
        self.params = kwargs
        self.state = State(output=0.0)
        self.input = Input() # This component has no inputs

        if self.signal_type == 'constant':
            self.state.output = self.params.get('value', 0.0)
        elif self.signal_type == 'step':
            self.state.output = self.params.get('initial_value', 0.0)
        else:
            raise ValueError(f"Unknown signal type: {self.signal_type}")

        self.output = self.state.output

    def step(self, t, **kwargs):
        """
        Updates the output based on the signal type and time.
        """
        if self.signal_type == 'step':
            step_time = self.params.get('step_time', float('inf'))
            if t >= step_time:
                self.state.output = self.params.get('step_value', 0.0)

        # For 'constant', the output never changes from its initial value.
        self.output = self.state.output

    def get_state(self):
        """Returns the current state of the component."""
        return self.state.__dict__
