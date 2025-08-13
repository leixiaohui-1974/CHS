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

        This method must be implemented by all subclasses. It should
        update the internal state of the model and return its primary output.
        """
        pass

    @abstractmethod
    def get_state(self):
        """
        Returns a dictionary of the model's current state.
        """
        pass
