import math
from .strategies import BaseRunoffModel

class RunoffCoefficientModel(BaseRunoffModel):
    """A simple runoff model based on a runoff coefficient."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.params = kwargs
        self.output = 0.0

    def calculate_runoff(self, rainfall: float, sub_basin_params: dict, dt: float) -> float:
        """Runoff is a direct fraction of precipitation."""
        # Update coefficient if it's in the dynamic params
        current_coeff = sub_basin_params.get("C", 0.5)
        runoff = rainfall * current_coeff
        self.output = max(0, runoff)
        return self.output

    def get_state(self):
        """Returns the model's current state."""
        return {"output": self.output}

class XinanjiangModel(BaseRunoffModel):
    """
    Implementation of the Xinanjiang rainfall-runoff model.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.params = kwargs
        # Initialize states. Parameters are passed in calculate_runoff.
        self.W = 0.0
        self.output = 0.0
        # Check for initial states passed in kwargs
        if 'states' in kwargs:
            # Note: initial_W depends on WM, which is a param.
            # This highlights a dependency that makes stateless calculation tricky.
            # A good compromise is to require WM as an init param if initial_W is not given.
            WM = self.params.get('WM', 100)
            self.W = kwargs['states'].get("initial_W", WM * 0.5)

    def calculate_runoff(self, rainfall: float, sub_basin_params: dict, dt: float) -> float:
        """
        Calculates runoff based on Xinanjiang model logic.
        Assumes 'evaporation' is provided in sub_basin_params if needed.
        """
        # Update parameters dynamically if they are provided
        WM = sub_basin_params.get("WM", 100)
        B = sub_basin_params.get("B", 0.3)
        IM = sub_basin_params.get("IM", 0.05)

        # Evaporation is not part of the new interface, so we need to handle it.
        # Let's assume evaporation is zero if not provided.
        evaporation = sub_basin_params.get("evaporation", 0.0) * dt

        # Evaporation is subtracted from soil moisture first.
        actual_evaporation = evaporation * (self.W / WM)
        self.W -= actual_evaporation

        runoff = 0
        if rainfall > 0:
            WMM = WM * (1 + B)

            if self.W >= WM:
                A = WMM
            else:
                A = WMM * (1 - math.pow(1 - self.W / WM, 1 / (1 + B)))

            if rainfall + A >= WMM:
                runoff = rainfall - (WM - self.W)
            else:
                runoff = rainfall + self.W - WM + WM * math.pow(1 - (rainfall + A) / WMM, 1 + B)

            runoff = max(0, runoff)
            self.W += rainfall - runoff

        self.W = max(0, min(self.W, WM))
        self.output = runoff
        return self.output

    def get_state(self):
        """Returns the model's current state."""
        return {"W": self.W, "output": self.output}

# Placeholder for SCSRunoffModel
class SCSRunoffModel(BaseRunoffModel):
    def calculate_runoff(self, rainfall: float, sub_basin_params: dict, dt: float) -> float:
        cn = sub_basin_params.get("CN", 75)
        s = (1000 / cn) - 10
        ia = 0.2 * s
        if rainfall > ia:
            runoff = ((rainfall - ia) ** 2) / (rainfall - ia + s)
        else:
            runoff = 0
        return runoff

# Placeholder for TankModel
class TankModel(BaseRunoffModel):
    def calculate_runoff(self, rainfall: float, sub_basin_params: dict, dt: float) -> float:
        # Simplified single-tank logic
        return rainfall * 0.6

# Placeholder for HYMODModel
class HYMODModel(BaseRunoffModel):
    def calculate_runoff(self, rainfall: float, sub_basin_params: dict, dt: float) -> float:
        return rainfall * 0.7

# Placeholder for GreenAmptRunoffModel
class GreenAmptRunoffModel(BaseRunoffModel):
    def calculate_runoff(self, rainfall: float, sub_basin_params: dict, dt: float) -> float:
        # Simplified logic
        infiltration_rate = sub_basin_params.get("ksat", 5.0) # mm/hr
        runoff = max(0, rainfall - infiltration_rate * dt)
        return runoff

# Placeholder for TOPMODEL
class TOPMODEL(BaseRunoffModel):
    def calculate_runoff(self, rainfall: float, sub_basin_params: dict, dt: float) -> float:
        return rainfall * 0.65

# Placeholder for WETSPAModel
class WETSPAModel(BaseRunoffModel):
    def calculate_runoff(self, rainfall: float, sub_basin_params: dict, dt: float) -> float:
        return rainfall * 0.75

# Placeholder for ShanbeiModel
class ShanbeiModel(BaseRunoffModel):
    def calculate_runoff(self, rainfall: float, sub_basin_params: dict, dt: float) -> float:
        return rainfall * 0.55

# Placeholder for HebeiModel
class HebeiModel(BaseRunoffModel):
    def calculate_runoff(self, rainfall: float, sub_basin_params: dict, dt: float) -> float:
        return rainfall * 0.6
