from .base_model import BaseModel

class ConstantHeadReservoir(BaseModel):
    """
    A simple boundary condition model that represents a reservoir with a constant water level (head).
    Its output is always the same, regardless of inputs.
    """
    def __init__(self, level: float):
        """
        Initializes the constant head reservoir.

        Args:
            level (float): The constant water level (head) in meters.
        """
        super().__init__()
        self.output = level  # The output is the constant level.

    def step(self):
        """
        The step method does nothing as the level is constant.
        """
        pass

    def get_state(self):
        """
        Returns the model's state.
        """
        return {
            "level": self.output,
            "output": self.output
        }
