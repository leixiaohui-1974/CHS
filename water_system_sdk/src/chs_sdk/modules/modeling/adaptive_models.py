from .integral_plus_delay_model import IntegralPlusDelayModel

class PiecewiseIntegralDelayModel(IntegralPlusDelayModel):
    """
    An Integral-Plus-Delay model whose gain parameter (K) is scheduled
    based on the current input value. This is useful for simulating
    non-linear systems in a piecewise linear fashion.

    NOTE: For simulation stability and simplicity, this implementation assumes
    that the time delay 'T' is constant across all models in the bank.
    Changing the delay would require re-initializing the input buffer, which
    is not handled here.
    """
    def __init__(self, model_bank: list, dt: float, initial_value: float = 0.0, **kwargs):
        """
        Args:
            model_bank (list): The bank of models. The 'T' value in all entries
                               should be the same.
            dt (float): The simulation time step.
            initial_value (float): The initial value of the input and output.
        """
        self.model_bank = sorted(model_bank, key=lambda x: x['threshold'])
        if not all(m['T'] == self.model_bank[0]['T'] for m in self.model_bank):
            raise ValueError("All models in the bank must have the same time delay 'T' for this plant model.")

        initial_model = self.model_bank[0]
        super().__init__(K=initial_model['K'], T=initial_model['T'], dt=dt, initial_value=initial_value, **kwargs)

    def _select_model_k(self, scheduling_variable: float) -> float:
        """Selects the appropriate model gain K from the bank."""
        for model in self.model_bank:
            if scheduling_variable < model['threshold']:
                return model['K']
        return self.model_bank[-1]['K']

    def step(self, **kwargs):
        """
        Processes one time step, first updating K based on the current input.
        """
        # The scheduling variable for the plant is its own inflow.
        current_inflow = self.input.inflow
        self.K = self._select_model_k(current_inflow)

        super().step(**kwargs)
