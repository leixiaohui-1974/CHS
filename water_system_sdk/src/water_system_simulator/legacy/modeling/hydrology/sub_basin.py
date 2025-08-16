from typing import Tuple

class SubBasin:
    """
    Represents a single sub-basin, acting as a data container for its properties.
    It holds the physical and model parameters for a specific area.
    """
    def __init__(self, id: str, area: float, coords: Tuple[float, float], params: dict):
        """
        Initializes a SubBasin object.

        Args:
            id (str): The unique identifier for the sub-basin.
            area (float): The area of the sub-basin in square kilometers.
            coords (Tuple[float, float]): The (x, y) coordinates of the sub-basin's centroid.
            params (dict): A dictionary containing all parameters for the sub-basin.
                           This can include runoff parameters (e.g., CN, WM) and
                           routing parameters (e.g., K, x). It's up to the
                           strategy implementations to extract what they need.
        """
        self.id = id
        self.area = area  # km^2
        self.coords = coords
        self.params = params
        # Add area to the params dict so strategies can easily access it
        self.params['area'] = area

    def __repr__(self):
        return f"SubBasin(id={self.id}, area={self.area}, coords={self.coords}, params={self.params})"
