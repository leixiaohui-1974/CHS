from ..modeling.base_model import BaseModel

class BaseController(BaseModel):
    """
    Abstract base class for all controller models.
    Inherits from BaseModel to be compatible with the simulation manager.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # step and get_state are already abstract in BaseModel,
    # so they don't need to be redeclared here.
    # Subclasses of BaseController will still be required to implement them.
