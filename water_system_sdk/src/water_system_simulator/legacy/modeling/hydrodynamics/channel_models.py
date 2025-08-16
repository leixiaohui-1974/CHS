from water_system_simulator.modeling.base_model import BaseModel

class SteadyChannelModel(BaseModel):
    """
    Placeholder for a steady-state channel model.
    Based on the energy equation and standard step method.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.output = 0.0

    def solve(self, **kwargs):
        raise NotImplementedError("SteadyChannelModel is not yet implemented.")

    def step(self, **kwargs):
        # Steady model uses solve(), not step()
        pass

    def get_state(self):
        return {"status": "not_implemented"}

class StVenantModel(BaseModel):
    """
    Placeholder for a high-precision transient channel model.
    Based on the full 1D Saint-Venant equations.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.output = 0.0

    def step(self, **kwargs):
        raise NotImplementedError("StVenantModel is not yet implemented.")

    def get_state(self):
        return {"status": "not_implemented"}
