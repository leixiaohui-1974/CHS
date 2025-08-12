from abc import ABC, abstractmethod

class RunoffModel(ABC):
    """Abstract base class for all runoff models."""

    def __init__(self, parameters):
        """
        Initializes the runoff model with its parameters.

        Args:
            parameters (dict): A dictionary of parameters required by the model.
        """
        self.params = parameters
        self.states = {}

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
