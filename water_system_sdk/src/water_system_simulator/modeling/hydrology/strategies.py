from abc import ABC, abstractmethod
from water_system_simulator.modeling.base_model import BaseModel

class BaseRunoffModel(BaseModel, ABC):
    """
    Abstract base class for all runoff models.
    It defines the interface for calculating runoff from rainfall.
    """

    @abstractmethod
    def calculate_runoff(self, rainfall: float, sub_basin_params: dict, dt: float) -> float:
        """
        Calculates the runoff for a single time step.

        Args:
            rainfall (float): The total rainfall in mm for the time step.
            sub_basin_params (dict): A dictionary of parameters for the sub-basin.
            dt (float): The time step duration in hours.

        Returns:
            float: The effective rainfall (runoff) in mm.
        """
        pass

class BaseRoutingModel(BaseModel, ABC):
    """
    Abstract base class for all routing models.
    It defines the interface for routing flow through a sub-basin.
    """

    @abstractmethod
    def route_flow(self, effective_rainfall: float, sub_basin_params: dict, dt: float) -> float:
        """
        Routes the effective rainfall to the sub-basin outlet.

        Args:
            effective_rainfall (float): The effective rainfall (runoff) in mm,
                                        as calculated by a runoff model.
            sub_basin_params (dict): A dictionary of parameters for the sub-basin,
                                     including area, etc.
            dt (float): The time step duration in hours.

        Returns:
            float: The outflow from the sub-basin in cubic meters per second (m^3/s).
        """
        pass
