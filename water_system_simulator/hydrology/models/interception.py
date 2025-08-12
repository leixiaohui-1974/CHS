class HumanActivityModel:
    """
    Simulates the impact of small engineering works (e.g., check dams)
    on runoff generation. This model acts as an interception layer before
    the main runoff model.
    """
    def __init__(self, parameters):
        """
        Initializes the human activity impact model.

        Args:
            parameters (dict): A dictionary containing model parameters:
                - initial_interception_capacity_mm: Max storage of small dams.
                - interception_decay_rate: Controls how fast capacity decays
                                           with cumulative effective rainfall.
        """
        self.params = parameters
        self.initial_capacity = self.params.get("initial_interception_capacity_mm", 10.0)
        self.decay_rate = self.params.get("interception_decay_rate", 0.05)

        # State variables
        self.current_capacity = self.initial_capacity
        self.current_storage = 0.0
        self.cumulative_effective_precip = 0.0

    def intercept(self, precipitation_mm):
        """
        Processes incoming precipitation, intercepting a portion of it and
        updating the model's state.

        Args:
            precipitation_mm (float): The raw precipitation for the time step.

        Returns:
            float: The effective precipitation after interception, to be passed
                   to the runoff model.
        """
        # 1. Determine available storage
        available_storage = self.current_capacity - self.current_storage
        if available_storage <= 0:
            return precipitation_mm

        # 2. Intercept rainfall
        can_be_intercepted = min(precipitation_mm, available_storage)
        self.current_storage += can_be_intercepted

        effective_precip = precipitation_mm - can_be_intercepted

        # 3. Update the dynamic capacity of the interception layer
        # The capacity decays as more effective rainfall gets through,
        # simulating the filling up of the watershed's small storage systems.
        self.cumulative_effective_precip += effective_precip

        # A simple exponential decay model for the capacity
        self.current_capacity = self.initial_capacity * \
                                 (1 - self.decay_rate) ** self.cumulative_effective_precip

        # Ensure capacity doesn't go below zero
        self.current_capacity = max(0, self.current_capacity)

        return effective_precip
