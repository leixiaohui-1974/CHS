import math
from .base import RunoffModel

class RunoffCoefficientModel(RunoffModel):
    """A simple runoff model based on a runoff coefficient."""

    def __init__(self, parameters):
        super().__init__(parameters)
        self.runoff_coeff = self.params.get("C", 0.5)

    def calculate_pervious_runoff(self, pervious_precipitation, evaporation):
        """Runoff is a direct fraction of precipitation on the pervious area."""
        runoff = pervious_precipitation * self.runoff_coeff
        return max(0, runoff)

class XinanjiangModel(RunoffModel):
    """
    Implementation of the Xinanjiang rainfall-runoff model.
    This version has been corrected for a more standard water balance calculation.
    """
    def __init__(self, parameters):
        super().__init__(parameters)
        # Model parameters
        self.WM = self.params.get("WM", 100)  # Soil moisture capacity
        self.B = self.params.get("B", 0.3)    # Exponent of storage capacity curve
        self.IM = self.params.get("IM", 0.05) # Impervious area fraction

        # Model states
        self.W = self.states.get("initial_W", self.WM * 0.5) # Initial soil moisture

    def calculate_pervious_runoff(self, pervious_precipitation, evaporation):
        """
        Calculates runoff from the pervious area based on Xinanjiang model logic.
        """
        P_pervious = pervious_precipitation
        E = evaporation

        # Evaporation is subtracted from soil moisture first.
        # Actual evaporation depends on potential evaporation and available water.
        actual_evaporation = E * (self.W / self.WM)
        self.W -= actual_evaporation

        R_pervious = 0
        # Now, add rainfall to soil moisture and calculate runoff
        if P_pervious > 0:
            # Calculate runoff based on the tension water capacity curve
            WMM = self.WM * (1 + self.B)

            # A is the tension water storage capacity at the current soil moisture W
            # This check prevents math domain errors if W > WM
            if self.W >= self.WM:
                A = WMM
            else:
                A = WMM * (1 - math.pow(1 - self.W / self.WM, 1 / (1 + self.B)))

            # If total water (rainfall + current tension water) exceeds max capacity, runoff occurs
            if P_pervious + A >= WMM:
                R_pervious = P_pervious - (self.WM - self.W)
            else:
                # Runoff is P - delta_W
                R_pervious = P_pervious + self.W - self.WM + self.WM * math.pow(1 - (P_pervious + A) / WMM, 1 + self.B)

            R_pervious = max(0, R_pervious)

            # Update soil moisture with net rainfall (P_pervious - R_pervious)
            self.W += P_pervious - R_pervious

        # Clamp soil moisture to its bounds [0, WM]
        self.W = max(0, min(self.W, self.WM))

        return R_pervious
