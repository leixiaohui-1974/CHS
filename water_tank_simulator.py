class WaterTank:
    def __init__(self, area, initial_level, max_level=20):
        self.area = area
        self.level = initial_level
        self.max_level = max_level

    def update(self, q_in, q_out, dt):
        """
        Updates the water level in the tank.

        Args:
            q_in (float): Inflow rate.
            q_out (float): Outflow rate.
            dt (float): Time step.
        """
        # Calculate the change in water level
        dh = (q_in - q_out) / self.area * dt

        # Update the water level
        self.level += dh

        # Ensure the water level does not exceed the maximum level or go below zero
        if self.level > self.max_level:
            self.level = self.max_level
        elif self.level < 0:
            self.level = 0

        return self.level
