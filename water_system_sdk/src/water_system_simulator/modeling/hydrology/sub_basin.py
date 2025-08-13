class SubBasin:
    """
    Represents a single sub-basin, acting as a data container for its properties.
    It holds the physical and model parameters for a specific area.
    """
    def __init__(self, area: float, params: dict):
        """
        Initializes a SubBasin object.

        Args:
            area (float): The area of the sub-basin in square kilometers.
            params (dict): A dictionary containing all parameters for the sub-basin.
                           This can include runoff parameters (e.g., CN, WM) and
                           routing parameters (e.g., K, x). It's up to the
                           strategy implementations to extract what they need.
        """
        self.area = area  # km^2
        self.params = params
        # Add area to the params dict so strategies can easily access it
        self.params['area'] = area

    def __repr__(self):
        return f"SubBasin(area={self.area}, params={self.params})"
