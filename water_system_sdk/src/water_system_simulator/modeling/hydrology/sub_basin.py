from water_system_sdk.src.water_system_simulator.modeling.hydrology.components.runoff import XinanjiangModel
from water_system_sdk.src.water_system_simulator.modeling.hydrology.components.routing import MuskingumModel

class SubBasin:
    """
    Represents a single sub-basin, which is the basic computational unit for the semi-distributed model.
    It encapsulates the runoff generation and routing processes for a specific area.
    """
    def __init__(self, area: float, initial_state: dict, runoff_params: dict, routing_params: dict):
        """
        Initializes a SubBasin object.

        Args:
            area (float): The area of the sub-basin in square kilometers.
            initial_state (dict): The initial state of the sub-basin's models.
            runoff_params (dict): Parameters for the runoff generation model (e.g., Xinanjiang).
            routing_params (dict): Parameters for the routing model (e.g., Muskingum).
        """
        self.area = area  # km^2
        self.runoff_model = XinanjiangModel(**runoff_params, initial_states=initial_state.get('runoff', {}))
        self.routing_model = MuskingumModel(params=routing_params, states=initial_state.get('routing', {}))

    def step(self, precipitation: float, evaporation: float, dt: float) -> float:
        """
        Performs a single time step calculation for the sub-basin.

        Args:
            precipitation (float): Precipitation rate in mm/hr.
            evaporation (float): Potential evaporation rate in mm/hr.
            dt (float): The time step in hours.

        Returns:
            float: The outflow from the sub-basin in cubic meters per second (m^3/s).
        """
        # 1. Calculate runoff from precipitation
        # Precipitation is in mm/hr, runoff is in mm
        pervious_precipitation = precipitation * dt
        runoff_depth_mm = self.runoff_model.calculate_pervious_runoff(pervious_precipitation, evaporation * dt)

        # 2. Convert runoff depth (mm) over the area (km^2) to inflow volume (m^3/s) for the routing model
        # Runoff (mm) * Area (km^2) * 1000 (m/km) * 1000 (m/km) / 1000 (mm/m) = m^3
        # Volume (m^3) / (dt * 3600 s/hr) = m^3/s
        inflow_m3_per_s = (runoff_depth_mm * self.area * 1000) / (dt * 3600)

        # 3. Route the inflow to get the outflow
        outflow_m3_per_s = self.routing_model.route(inflow_m3_per_s)

        return outflow_m3_per_s

    def get_state(self):
        """
        Returns the current state of the sub-basin's internal models.
        """
        return {
            "runoff": self.runoff_model.get_state(),
            "routing": self.routing_model.get_state(),
        }
