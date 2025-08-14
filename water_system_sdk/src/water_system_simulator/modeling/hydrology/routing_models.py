from typing import Dict, Any
import numpy as np
from numba import njit
from .strategies import BaseRoutingModel

@njit
def _muskingum_route_jitted(effective_rainfall_vector, I_prev, O_prev, params, dt):
    """Jitted and vectorized Muskingum routing calculation."""
    # Extract parameter vectors
    K = params['K']
    x = params['x']
    area_km2 = params['area']

    # Vectorized conversion from effective rainfall (mm) to inflow (m^3/s)
    inflow_m3_per_s = (effective_rainfall_vector * area_km2 * 1000) / (dt * 3600)

    I_t = inflow_m3_per_s

    # Calculate coefficients dynamically
    denominator = 2 * K * (1 - x) + dt
    C1 = (dt - 2 * K * x) / denominator
    C2 = (dt + 2 * K * x) / denominator
    C3 = (2 * K * (1 - x) - dt) / denominator

    # Vectorized Muskingum equation
    O_t = C1 * I_t + C2 * I_prev + C3 * O_prev

    # Ensure non-negative outflow
    O_t = np.maximum(O_t, 0.0)

    # Return new states
    I_new = I_t
    O_new = O_t

    return O_t, I_new, O_new

class MuskingumModel(BaseRoutingModel):
    """
    Implements the Muskingum method for river routing.
    Includes both original and vectorized methods.
    """
    def __init__(self, **kwargs):
        # This model is now effectively stateless for the vectorized path.
        # Restore state init for non-vectorized path to pass unit tests
        self.I_prev = 0.0
        self.O_prev = 0.0
        self.output = 0.0
        if 'states' in kwargs:
            self.I_prev = kwargs['states'].get("initial_inflow", 0.0)
            self.O_prev = kwargs['states'].get("initial_outflow", 0.0)

    def route_flow_vectorized(self, effective_rainfall_vector, I_prev, O_prev, params, dt):
        """
        Wrapper for the jitted vectorized Muskingum calculation.
        """
        return _muskingum_route_jitted(effective_rainfall_vector, I_prev, O_prev, params, dt)

    def route_flow(self, effective_rainfall: float, sub_basin_params: Dict[str, Any], dt: float) -> float:
        """
        Routes the inflow for one time step using Muskingum method.
        """
        # Get parameters from sub_basin_params, with defaults
        K = float(sub_basin_params.get("K", 24))
        x = float(sub_basin_params.get("x", 0.2))
        area_km2 = sub_basin_params.get("area")

        if area_km2 is None:
            raise ValueError("Muskingum routing requires 'area' in sub_basin_params.")

        # Convert effective rainfall (mm) over the area (km^2) to inflow (m^3/s)
        # Rainfall (mm) -> 0.001 m
        # Area (km^2) -> 1,000,000 m^2
        # Volume (m^3) = effective_rainfall * 0.001 * area_km2 * 1,000,000
        #              = effective_rainfall * area_km2 * 1000
        # Inflow (m^3/s) = Volume / (dt * 3600)
        inflow_m3_per_s = (effective_rainfall * area_km2 * 1000) / (dt * 3600)

        I_t = inflow_m3_per_s

        # Calculate coefficients dynamically, as dt might change
        denominator = 2 * K * (1 - x) + dt
        C1 = (dt - 2 * K * x) / denominator
        C2 = (dt + 2 * K * x) / denominator
        C3 = (2 * K * (1 - x) - dt) / denominator

        # Muskingum equation: O_t = C1*I_t + C2*I_{t-1} + C3*O_{t-1}
        O_t = C1 * I_t + C2 * self.I_prev + C3 * self.O_prev

        self.output = max(0, O_t)

        # Update states for the next time step
        self.I_prev = I_t
        self.O_prev = self.output

        return self.output

    def get_state(self):
        """Returns the model's current state."""
        return {
            "I_prev": self.I_prev,
            "O_prev": self.O_prev,
            "output": self.output
        }

# Placeholder for UnitHydrographRoutingModel
class UnitHydrographRoutingModel(BaseRoutingModel):
    def route_flow(self, effective_rainfall: float, sub_basin_params: Dict[str, Any], dt: float) -> float:
        # This requires convolution, which is complex for a simple placeholder.
        # For now, we'll just pass through the inflow.
        area_km2 = sub_basin_params.get("area")
        if area_km2 is None:
            raise ValueError("UnitHydrographRoutingModel requires 'area' in sub_basin_params.")
        inflow_m3_per_s = (effective_rainfall * area_km2 * 1000) / (dt * 3600)
        return float(inflow_m3_per_s)

# Placeholder for LinearReservoirRoutingModel
class LinearReservoirRoutingModel(BaseRoutingModel):
    def route_flow(self, effective_rainfall: float, sub_basin_params: Dict[str, Any], dt: float) -> float:
        # Simplified logic
        area_km2 = sub_basin_params.get("area")
        if area_km2 is None:
            raise ValueError("LinearReservoirRoutingModel requires 'area' in sub_basin_params.")
        inflow_m3_per_s = (effective_rainfall * area_km2 * 1000) / (dt * 3600)
        k = float(sub_basin_params.get("k_res", 12)) # storage constant
        # O_t = O_{t-1} + (dt/k)*(I_avg - O_{t-1}) -> Simplified, assumes O_prev is stored
        return inflow_m3_per_s * 0.8 # Pass-through with damping

# Placeholder for VariableVolumeRoutingModel
class VariableVolumeRoutingModel(BaseRoutingModel):
    def route_flow(self, effective_rainfall: float, sub_basin_params: Dict[str, Any], dt: float) -> float:
        # This is a complex method, placeholder will just pass through inflow.
        area_km2 = sub_basin_params.get("area")
        if area_km2 is None:
            raise ValueError("VariableVolumeRoutingModel requires 'area' in sub_basin_params.")
        inflow_m3_per_s = (effective_rainfall * area_km2 * 1000) / (dt * 3600)
        return float(inflow_m3_per_s)
