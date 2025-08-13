class State:
    """A generic container for a component's state variables."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        return f"State({self.__dict__})"

class Input:
    """A generic container for a component's input variables."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        return f"Input({self.__dict__})"
