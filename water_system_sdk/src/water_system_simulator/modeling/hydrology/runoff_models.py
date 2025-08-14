import math
from typing import Dict, Any
import numpy as np
from numba import njit
from .strategies import BaseRunoffModel

@njit
def _xinanjiang_runoff_jitted(rainfall_vector, W_initial, WM, B, IM):
    """Jitted and vectorized Xinanjiang runoff calculation."""
    num_basins = len(rainfall_vector)
    runoff = np.zeros(num_basins, dtype=np.float32)
    W = W_initial.copy() # Make a mutable copy of the state

    # Evaporation is not included in this simplified vectorized version yet
    # It would require another vector input

    WMM = WM * (1 + B)

    for i in range(num_basins):
        if rainfall_vector[i] > 0:
            # Calculate A based on current moisture W[i] and max capacity WM[i]
            if W[i] >= WM[i]:
                A = WMM[i]
            else:
                A = WMM[i] * (1 - math.pow(1 - W[i] / WM[i], 1 / (1 + B[i])))

            # Calculate runoff based on rainfall and A
            if rainfall_vector[i] + A >= WMM[i]:
                current_runoff = rainfall_vector[i] - (WM[i] - W[i])
            else:
                term = 1 - (rainfall_vector[i] + A) / WMM[i]
                current_runoff = rainfall_vector[i] + W[i] - WM[i] + WM[i] * math.pow(term, 1 + B[i])

            runoff[i] = max(0, current_runoff)
            W[i] += rainfall_vector[i] - runoff[i]
            W[i] = max(0, min(W[i], WM[i]))

    return runoff, W


class RunoffCoefficientModel(BaseRunoffModel):
    """A simple runoff model based on a runoff coefficient."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.params = kwargs
        self.output = 0.0

    def calculate_runoff(self, rainfall: float, sub_basin_params: Dict[str, Any], dt: float) -> float:
        """Runoff is a direct fraction of precipitation."""
        # Update coefficient if it's in the dynamic params
        current_coeff = float(sub_basin_params.get("C", 0.5))
        runoff = rainfall * current_coeff
        self.output = max(0, runoff)
        return self.output

    def get_state(self):
        """Returns the model's current state."""
        return {"output": self.output}

class XinanjiangModel(BaseRunoffModel):
    """
    Implementation of the Xinanjiang rainfall-runoff model.
    Includes both original and vectorized methods.
    """
    def __init__(self, **kwargs):
        # This model is now effectively stateless for the vectorized path.
        # The state is managed by the orchestrator (e.g., SemiDistributedHydrologyModel)
        self.params = kwargs
        # Restore state init for non-vectorized path to pass unit tests
        self.W = 0.0
        self.output = 0.0
        if 'states' in kwargs:
            WM = self.params.get('WM', 100)
            self.W = kwargs['states'].get("initial_W", WM * 0.5)

    def calculate_runoff_vectorized(self, rainfall_vector, W_initial, params, dt):
        """
        Wrapper for the jitted vectorized Xinanjiang calculation.

        Args:
            rainfall_vector (np.ndarray): Vector of rainfall for each sub-basin.
            W_initial (np.ndarray): The initial soil moisture state vector.
            params (np.ndarray): The structured array of parameters for all sub-basins.
            dt (float): Time step.

        Returns:
            Tuple[np.ndarray, np.ndarray]: A tuple containing the runoff vector and the updated state vector.
        """
        # Extract parameter vectors from the structured array
        WM = params['WM']
        B = params['B']
        IM = params['IM']

        runoff, W_new = _xinanjiang_runoff_jitted(rainfall_vector, W_initial, WM, B, IM)
        return runoff, W_new

    def calculate_runoff(self, rainfall: float, sub_basin_params: Dict[str, Any], dt: float) -> float:
        """
        Calculates runoff based on Xinanjiang model logic.
        Assumes 'evaporation' is provided in sub_basin_params if needed.
        """
        # Update parameters dynamically if they are provided
        WM = float(sub_basin_params.get("WM", 100))
        B = float(sub_basin_params.get("B", 0.3))
        IM = float(sub_basin_params.get("IM", 0.05))

        # Evaporation is not part of the new interface, so we need to handle it.
        # Let's assume evaporation is zero if not provided.
        evaporation = float(sub_basin_params.get("evaporation", 0.0)) * dt

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
    def calculate_runoff(self, rainfall: float, sub_basin_params: Dict[str, Any], dt: float) -> float:
        cn = float(sub_basin_params.get("CN", 75))
        s = (1000 / cn) - 10
        ia = 0.2 * s
        if rainfall > ia:
            runoff = ((rainfall - ia) ** 2) / (rainfall - ia + s)
        else:
            runoff = 0
        return runoff

# Placeholder for TankModel
class TankModel(BaseRunoffModel):
    def calculate_runoff(self, rainfall: float, sub_basin_params: Dict[str, Any], dt: float) -> float:
        # Simplified single-tank logic
        return rainfall * 0.6

# Placeholder for HYMODModel
class HYMODModel(BaseRunoffModel):
    def calculate_runoff(self, rainfall: float, sub_basin_params: Dict[str, Any], dt: float) -> float:
        return rainfall * 0.7

# Placeholder for GreenAmptRunoffModel
class GreenAmptRunoffModel(BaseRunoffModel):
    def calculate_runoff(self, rainfall: float, sub_basin_params: Dict[str, Any], dt: float) -> float:
        # Simplified logic
        infiltration_rate = float(sub_basin_params.get("ksat", 5.0)) # mm/hr
        runoff = max(0, rainfall - infiltration_rate * dt)
        return runoff

# Placeholder for TOPMODEL
class TOPMODEL(BaseRunoffModel):
    def calculate_runoff(self, rainfall: float, sub_basin_params: Dict[str, Any], dt: float) -> float:
        return rainfall * 0.65

# Placeholder for WETSPAModel
class WETSPAModel(BaseRunoffModel):
    def calculate_runoff(self, rainfall: float, sub_basin_params: Dict[str, Any], dt: float) -> float:
        return rainfall * 0.75

# Placeholder for ShanbeiModel
class ShanbeiModel(BaseRunoffModel):
    def calculate_runoff(self, rainfall: float, sub_basin_params: Dict[str, Any], dt: float) -> float:
        return rainfall * 0.55

# Placeholder for HebeiModel
class HebeiModel(BaseRunoffModel):
    def calculate_runoff(self, rainfall: float, sub_basin_params: Dict[str, Any], dt: float) -> float:
        return rainfall * 0.6
