from abc import ABC, abstractmethod

class BaseController(ABC):
    """
    Abstract base class for all controller models.
    """
    def __init__(self, **kwargs):
        self.output = None
        super().__init__()

    @abstractmethod
    def calculate(self, *args, **kwargs):
        """
        Represents a single time step of the controller's execution.

        This method must be implemented by all subclasses. It should
        calculate the control action and return it.
        """
        pass
