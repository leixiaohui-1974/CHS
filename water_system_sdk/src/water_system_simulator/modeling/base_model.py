from abc import ABC, abstractmethod

class BaseModel(ABC):
    """
    Abstract base class for all water system simulation models.
    """
    def __init__(self, **kwargs):
        # The output attribute should be initialized by all child classes.
        self.output = None
        super().__init__()

    @abstractmethod
    def step(self, *args, **kwargs):
        """
        Represents a single time step of the model's execution.

        This method must be implemented by subclasses. It can accept
        any arguments required for the simulation step.
        """
        pass

    @abstractmethod
    def get_state(self):
        """
        Returns a dictionary of the model's current state.
        This must be implemented by subclasses.
        """
        pass

