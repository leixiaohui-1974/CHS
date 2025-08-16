import numpy as np
from .actuator_models import ActuatorBase
from typing import Callable

class TurbineBase(ActuatorBase):
    """
    Base class for hydraulic turbine models.
    The actuator controls the guide vane / needle opening (0-1).
    """
    def __init__(self, initial_opening: float = 0.0, **kwargs):
        super().__init__(initial_position=initial_opening, **kwargs)
        self.flow = 0.0
        self.power = 0.0
        self.efficiency = 0.0
        self.output = self.flow

    def set_opening(self, opening: float):
        """
        Set the target opening of the turbine.

        Args:
            opening (float): The desired opening as a fraction (0.0 to 1.0).
        """
        self.set_target(np.clip(opening, 0, 1))

    def get_current_opening(self) -> float:
        """Returns the current operating opening as a fraction (0-1)."""
        return np.clip(self.get_current_position(), 0, 1)

    def step(self, head: float, dt: float, **kwargs):
        """
        Updates the turbine's state and calculates flow and power.
        Must be implemented by subclasses.
        """
        raise NotImplementedError


class FrancisTurbine(TurbineBase):
    """
    A Francis (mixed-flow) turbine model.
    Requires a comprehensive efficiency map (hill chart) for accurate simulation.
    efficiency = f(Head, Flow)
    """
    def __init__(self,
                 flow_coeff_curve: Callable[[float], float], # Flow coeff K_Q = f(opening)
                 efficiency_map: Callable[[float, float], float], # efficiency = f(Head, Q)
                 **kwargs):
        super().__init__(**kwargs)
        self.flow_coeff_curve = flow_coeff_curve # K_Q where Q = K_Q * sqrt(H)
        self.efficiency_map = efficiency_map

    def step(self, head: float, dt: float, **kwargs):
        self.update(dt)
        opening = self.get_current_opening()

        if head <= 0 or opening <= 0:
            self.flow = self.power = self.efficiency = 0.0
            self.output = self.flow
            return self.output

        # Calculate flow: Q = K_Q(opening) * sqrt(H)
        k_q = self.flow_coeff_curve(opening)
        self.flow = k_q * np.sqrt(head)

        # Calculate efficiency and power
        self.efficiency = self.efficiency_map(head, self.flow)
        g = 9.81
        rho = 1000
        self.power = self.efficiency * rho * g * self.flow * head

        self.output = self.flow
        return self.output

class KaplanTurbine(FrancisTurbine):
    """
    A Kaplan (axial-flow) turbine with dual regulation (guide vanes and runner blades).
    This simplified model assumes the runner blade pitch is optimally adjusted,
    so its efficiency curve is flatter than a Francis turbine's.
    It can be represented by the same model, but with a different efficiency_map.
    """
    pass

class PeltonTurbine(TurbineBase):
    """
    A Pelton (impulse) turbine, for high head applications.
    Flow is controlled by a needle valve (spear).
    """
    def __init__(self,
                 flow_coeff: float, # Q = K * opening * sqrt(H)
                 efficiency_curve: Callable[[float], float], # eff = f(flow_ratio)
                 rated_flow: float,
                 **kwargs):
        super().__init__(**kwargs)
        self.flow_coeff = flow_coeff
        self.efficiency_curve = efficiency_curve
        self.rated_flow = rated_flow

    def step(self, head: float, dt: float, **kwargs):
        self.update(dt)
        opening = self.get_current_opening()

        if head <= 0 or opening <= 0:
            self.flow = self.power = self.efficiency = 0.0
            self.output = self.flow
            return self.output

        # Flow is proportional to needle opening and sqrt(Head)
        self.flow = self.flow_coeff * opening * np.sqrt(head)

        # Efficiency depends on the ratio of actual flow to rated flow
        flow_ratio = self.flow / self.rated_flow if self.rated_flow > 0 else 0
        self.efficiency = self.efficiency_curve(flow_ratio)

        g = 9.81
        rho = 1000
        self.power = self.efficiency * rho * g * self.flow * head

        self.output = self.flow
        return self.output
