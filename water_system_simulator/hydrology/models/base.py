from abc import ABC, abstractmethod

from ...modeling.base_model import BaseModel

class RunoffModel(BaseModel, ABC):
    """Abstract base class for all runoff models."""

    def __init__(self, **kwargs):
        """
        Initializes the runoff model with its parameters.
        """
        super().__init__(**kwargs)
        self.params = kwargs
        self.states = self.params.get("initial_states", {})
        self.pervious_runoff = 0.0
        self.impervious_runoff = 0.0

    @abstractmethod
    def calculate_pervious_runoff(self, pervious_precipitation, evaporation):
        """
        Calculates the amount of runoff generated from the pervious area.

        Args:
            pervious_precipitation (float): Precipitation falling on the pervious area.
            evaporation (float): Potential evaporation for the current time step.

        Returns:
            float: The generated runoff from the pervious area.
        """
        pass

    def calculate_impervious_runoff(self, impervious_precipitation):
        """Runoff from impervious area is total precipitation on that area."""
        return impervious_precipitation

    def step(self, precipitation: float, evaporation: float, **kwargs):
        """
        The step method called by the simulation engine.
        Connects to 'precipitation' and 'evaporation' disturbances.
        Calculates total runoff from pervious and impervious areas.
        """
        impervious_fraction = self.params.get("IM", 0.0)
        pervious_fraction = 1.0 - impervious_fraction

        pervious_precip = precipitation * pervious_fraction
        impervious_precip = precipitation * impervious_fraction

        self.pervious_runoff = self.calculate_pervious_runoff(pervious_precip, evaporation)
        self.impervious_runoff = self.calculate_impervious_runoff(impervious_precip)

        total_runoff = self.pervious_runoff + self.impervious_runoff
        self.output = total_runoff

        return self.output

class RoutingModel(ABC):
    """Abstract base class for all routing models."""

    def __init__(self, parameters):
        """
        Initializes the routing model with its parameters.

        Args:
            parameters (dict): A dictionary of parameters required by the model.
        """
        self.params = parameters
        self.states = {}

    @abstractmethod
    def route(self, inflow):
        """
        Routes an inflow through a river reach or channel.

        Args:
            inflow (float): The inflow volume or flow rate for the current time step.

        Returns:
            float: The routed outflow for the current time step.
        """
        pass
