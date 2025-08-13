class HumanActivityModel:
    """A placeholder for the HumanActivityModel."""
    def __init__(self, params):
        self.capacity = params.get("initial_interception_capacity_mm", 0.0)

    def intercept(self, rainfall):
        """A placeholder for the intercept method."""
        intercepted = min(rainfall, self.capacity)
        self.capacity -= intercepted
        return rainfall - intercepted
