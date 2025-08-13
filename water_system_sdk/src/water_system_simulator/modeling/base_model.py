from abc import ABC, abstractmethod

class BaseModel(ABC):
    """
    Abstract base class for all water system simulation models.
    """
    def __init__(self, **kwargs):
        # The output attribute should be initialized by all child classes.
        self.output = None
        super().__init__()

    def step(self, dt, t):
        """
        Represents a single time step of the model's execution.

        This method can be implemented by subclasses that need to perform
        time-based updates.
        """
        pass

    def get_state(self):
        """
        Returns a dictionary of the model's current state.
        This can be overridden by subclasses to expose their state.
        """
        # Return all instance attributes as the default state
        return {key: value for key, value in self.__dict__.items() if not key.startswith('_')}

    @property
    def state(self):
        """
        A property to access the model's state using dot notation, e.g., model.state.
        This is useful for the connection logic in the SimulationManager.
        """
        return self.get_state()
