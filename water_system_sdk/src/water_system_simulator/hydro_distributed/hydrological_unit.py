import numpy as np

class HydrologicalUnit:
    """
    Represents a single grid cell (hydrological unit) in the watershed.

    This class is responsible for all vertical water balance calculations
    at the cell level using a multi-bucket model. The soil storage capacity
    is parameterized using the SCS Curve Number.
    """
    def __init__(self, curve_number: int, interception_max_storage: float = 1.5, initial_soil_moisture_ratio: float = 0.5, **kwargs):
        """
        Initializes a hydrological unit.

        Args:
            curve_number (int): The SCS Curve Number (1-100). Determines soil storage.
            interception_max_storage (float): Max interception storage (e.g., for canopy) in mm.
            initial_soil_moisture_ratio (float): The initial soil moisture as a fraction of max storage (0-1).
            **kwargs: Other parameters like land_use, soil_type, slope.
        """
        if not (0 < curve_number <= 100):
            raise ValueError("Curve Number must be between 1 and 100.")

        self.params = kwargs
        self.cn = curve_number

        # Parameterize soil storage capacity based on CN.
        # S = (1000/CN - 10) inches. This S is a good measure of total potential soil retention.
        self.soil_max_storage = (1000.0 / self.cn - 10.0) * 25.4

        # State variables
        self.interception_max_storage = interception_max_storage
        self.interception_storage = 0.0  # Current water on canopy (mm)
        self.soil_moisture = self.soil_max_storage * initial_soil_moisture_ratio # (mm)

    def update_state(self, rainfall_mm: float, pot_et_mm: float):
        """
        Updates the state of the hydrological unit for one time step.

        Args:
            rainfall_mm (float): Total rainfall in this timestep (mm).
            pot_et_mm (float): Potential evapotranspiration in this timestep (mm).

        Returns:
            float: The surface runoff generated in this time step (mm).
        """
        # --- 1. Evapotranspiration ---
        # First, ET from interception storage
        et_from_interception = min(self.interception_storage, pot_et_mm)
        self.interception_storage -= et_from_interception
        remaining_et = pot_et_mm - et_from_interception

        # Then, ET from soil moisture
        et_from_soil = min(self.soil_moisture, remaining_et)
        self.soil_moisture -= et_from_soil

        # --- 2. Interception ---
        # How much of the new rainfall can the canopy intercept?
        to_intercept = min(rainfall_mm, self.interception_max_storage - self.interception_storage)
        self.interception_storage += to_intercept
        throughfall = rainfall_mm - to_intercept

        # --- 3. Infiltration and Runoff ---
        # How much space is available in the soil?
        available_soil_storage = self.soil_max_storage - self.soil_moisture

        # Infiltration is the lesser of what's available (throughfall) and what the soil can hold
        infiltration = min(throughfall, available_soil_storage)
        self.soil_moisture += infiltration

        # Surface runoff is the throughfall that could not infiltrate
        surface_runoff_mm = throughfall - infiltration

        return surface_runoff_mm
