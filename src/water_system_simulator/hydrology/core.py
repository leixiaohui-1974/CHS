import numpy as np
from .utils.file_parsers import (
    load_topology_from_json,
    load_parameters_from_json,
    load_timeseries_from_json,
)
from .models.runoff import RunoffCoefficientModel, XinanjiangModel
from .models.routing import MuskingumModel
from .models.interception import HumanActivityModel

# --- Model Factories ---
RUNOFF_MODEL_MAP = {
    "RunoffCoefficient": RunoffCoefficientModel,
    "Xinanjiang": XinanjiangModel,
}

ROUTING_MODEL_MAP = {
    "Muskingum": MuskingumModel,
}

# --- Core Hydrological Components ---

class SubBasin:
    """Represents a single sub-basin in the watershed."""
    def __init__(self, element_id, area_km2, params):
        self.id = element_id
        self.area_km2 = area_km2

        # --- Runoff Model ---
        runoff_model_name = params.get("runoff_model", "default")
        if runoff_model_name not in RUNOFF_MODEL_MAP:
            raise ValueError(f"Runoff model '{runoff_model_name}' not found for {self.id}")
        self.runoff_model = RUNOFF_MODEL_MAP[runoff_model_name](params.get("runoff_parameters", {}))

        # --- Human Activity Interception Model (Optional) ---
        self.interception_model = None
        if params.get("human_activity_model", {}).get("enabled", False):
            interception_params = params["human_activity_model"].get("parameters", {})
            self.interception_model = HumanActivityModel(interception_params)

        self.inflow = 0.0  # Inflow from upstream elements
        self.outflow = 0.0 # Outflow from this sub-basin (runoff + routed inflow)

    def calculate_runoff(self, precipitation_mm, evaporation_mm, dt_hours):
        """
        Calculates the total runoff from the sub-basin for a time step.
        This method now correctly orchestrates the impervious/pervious split,
        interception, and pervious runoff calculation.
        """
        # --- 1. Impervious Area Runoff ---
        # Runoff from impervious areas is immediate and not subject to interception.
        # We need the impervious fraction (IM) from the runoff model parameters.
        impervious_fraction = self.runoff_model.params.get("IM", 0.0)
        impervious_runoff_depth = precipitation_mm * impervious_fraction

        # --- 2. Pervious Area Rainfall ---
        # This is the rainfall that is subject to interception and infiltration.
        pervious_precip_mm = precipitation_mm * (1 - impervious_fraction)

        # --- 3. Apply Interception Model (if it exists) ---
        # The interception model simulates storage in small dams and vegetation.
        if self.interception_model:
            pervious_precip_mm = self.interception_model.intercept(pervious_precip_mm)

        # --- 4. Pervious Area Runoff ---
        # The (potentially reduced) pervious rainfall is passed to the runoff model.
        pervious_runoff_depth = self.runoff_model.calculate_pervious_runoff(
            pervious_precip_mm, evaporation_mm
        )

        # --- 5. Total Runoff and Unit Conversion ---
        total_runoff_depth_mm = impervious_runoff_depth + pervious_runoff_depth

        # Convert runoff depth (mm) over the area (km2) to flow rate (m3/s)
        volume_m3 = total_runoff_depth_mm * self.area_km2 * 1000
        flow_rate_m3s = volume_m3 / (dt_hours * 3600)

        return flow_rate_m3s

class Reservoir:
    """Represents a reservoir in the watershed."""
    def __init__(self, element_id, params):
        self.id = element_id
        self.params = params
        self.storage_m3 = params.get("initial_storage_m3", 0)
        self.time_constant_hr = self.params.get("time_constant_hr", 24)

        self.inflow = 0.0  # m3/s
        self.outflow = 0.0 # m3/s

    def step(self, dt_hours):
        """
        Performs a single simulation step for the reservoir.
        Uses a simple linear reservoir model for now.
        """
        # Update storage based on inflow over the time step
        self.storage_m3 += self.inflow * dt_hours * 3600

        # Linear reservoir model: outflow (m3/s) is proportional to storage
        # Outflow = Storage / TimeConstant
        # We need to be careful with units. Storage is m3, TC is hours.
        # Outflow (m3/s) = Storage (m3) / (TimeConstant (hr) * 3600 (s/hr))
        self.outflow = self.storage_m3 / (self.time_constant_hr * 3600)

        # Update storage based on outflow
        self.storage_m3 -= self.outflow * dt_hours * 3600

        self.inflow = 0 # Reset inflow for next step
        return self.outflow

class Reach:
    """Represents a river reach, connecting two elements and performing routing."""
    def __init__(self, from_id, to_id, model_name, params):
        self.from_id = from_id
        self.to_id = to_id

        if model_name not in ROUTING_MODEL_MAP:
            raise ValueError(f"Routing model '{model_name}' not found for reach {from_id}->{to_id}")

        self.routing_model = ROUTING_MODEL_MAP[model_name](params)

    def route(self, inflow):
        return self.routing_model.route(inflow)

# --- Main Orchestrator ---

class Basin:
    """The main orchestrator for the hydrological simulation."""
    def __init__(self, topology_data, params_data, timeseries_data):
        self.topology_data = topology_data
        self.params_data = params_data
        self.timeseries_data = timeseries_data

        self.elements = {} # Dict of SubBasin and Reservoir objects
        self.reaches = {}  # Dict of Reach objects, key is the 'from_id'
        self.simulation_order = []

        self._build_basin()
        self._topological_sort()

    def _build_basin(self):
        """Constructs the basin network from the loaded configuration."""
        for element_data in self.topology_data["elements"]:
            element_id = element_data["id"]
            params = self.params_data.get(element_id, {})

            # Create SubBasins and Reservoirs
            if element_data["type"] == "sub_basin":
                self.elements[element_id] = SubBasin(
                    element_id=element_id,
                    area_km2=element_data["area_km2"],
                    params=params
                )
            elif element_data["type"] == "reservoir":
                self.elements[element_id] = Reservoir(
                    element_id=element_id,
                    params=params.get("parameters", {})
                )

            # Create Reaches for routing
            downstream_id = element_data["downstream"]
            if downstream_id and downstream_id not in self.topology_data["sinks"]:
                self.reaches[element_id] = Reach(
                    from_id=element_id,
                    to_id=downstream_id,
                    model_name=params.get("routing_model", "default"),
                    params=params.get("routing_parameters", {})
                )

    def _topological_sort(self):
        """Performs a topological sort to determine the simulation order."""
        graph = {el_id: [] for el_id in self.elements}
        in_degree = {el_id: 0 for el_id in self.elements}

        for el_id, reach in self.reaches.items():
            graph[el_id].append(reach.to_id)
            in_degree[reach.to_id] += 1

        queue = [el_id for el_id in self.elements if in_degree[el_id] == 0]

        while queue:
            u = queue.pop(0)
            self.simulation_order.append(u)

            if u in graph:
                for v in graph[u]:
                    in_degree[v] -= 1
                    if in_degree[v] == 0:
                        queue.append(v)

        if len(self.simulation_order) != len(self.elements):
            raise Exception("Cycle detected in basin topology, cannot determine simulation order.")

    def run_simulation(self):
        """Runs the full hydrological simulation."""
        dt_hours = self.timeseries_data["time_step_hours"]
        num_steps = len(self.timeseries_data["data"]["SubBasin1"]["precipitation_mm"])

        results = {el_id: np.zeros(num_steps) for el_id in self.elements}

        for t in range(num_steps):
            for element_id in self.simulation_order:
                element = self.elements[element_id]

                local_outflow = 0
                if isinstance(element, SubBasin):
                    precip = self.timeseries_data["data"][element_id]["precipitation_mm"][t]
                    evap = self.timeseries_data["data"][element_id]["evaporation_mm"][t]
                    local_outflow = element.calculate_runoff(precip, evap, dt_hours)

                # Total inflow to the element is its local runoff plus inflow from upstream
                total_inflow_to_element_outlet = local_outflow + element.inflow

                # Now, route this total flow through the reach to the next element
                if element_id in self.reaches:
                    reach = self.reaches[element_id]
                    routed_outflow = reach.route(total_inflow_to_element_outlet)

                    # Add the routed flow to the downstream element's inflow for the next step
                    downstream_element = self.elements[reach.to_id]
                    downstream_element.inflow += routed_outflow

                    results[element_id][t] = routed_outflow
                else:
                    # This is a sink node
                    results[element_id][t] = total_inflow_to_element_outlet

        return results
