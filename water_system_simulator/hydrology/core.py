import numpy as np
from .utils.file_parsers import (
    load_topology_from_json,
    load_parameters_from_json,
    load_timeseries_from_json,
)
from .models.runoff import RunoffCoefficientModel, XinanjiangModel
from .models.routing import MuskingumModel
from .models.interception import HumanActivityModel
from .models.reservoir import RegulatedReservoir

# --- Model Factories ---
RUNOFF_MODEL_MAP = {
    "RunoffCoefficient": RunoffCoefficientModel,
    "Xinanjiang": XinanjiangModel,
}

ROUTING_MODEL_MAP = {
    "Muskingum": MuskingumModel,
}

RESERVOIR_MODEL_MAP = {
    "RegulatedReservoir": RegulatedReservoir
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
        self.outflow = 0.0 # Outflow from this sub-basin
        self.storage = 0.0 # Internal storage for routing inflow

    def step(self, precip_mm, evap_mm, dt_hours):
        """
        Performs a single simulation step for the sub-basin.
        It calculates its own local runoff and then routes the total inflow
        (local runoff + upstream inflow) through a simple linear storage model.
        """
        local_runoff_m3s = self.calculate_local_runoff(precip_mm, evap_mm, dt_hours)

        total_inflow_m3s = local_runoff_m3s + self.inflow

        # Simple linear storage model to route the total flow
        # T is a time constant for the sub-basin, can be parameterized
        T_hours = 12 # Assume a 12-hour residence time

        # Update storage
        self.storage += (total_inflow_m3s - self.outflow) * dt_hours * 3600
        self.storage = max(0, self.storage)

        # Calculate new outflow
        self.outflow = self.storage / (T_hours * 3600)

        self.inflow = 0 # Reset inflow for next step
        return self.outflow

    def calculate_local_runoff(self, precipitation_mm, evaporation_mm, dt_hours):
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
    """Represents a reservoir in the watershed, acting as a wrapper for a specific reservoir model."""
    def __init__(self, element_id, params):
        self.id = element_id
        self.params = params

        # --- Reservoir Model ---
        storage_model_name = params.get("storage_model", "default")
        if storage_model_name not in RESERVOIR_MODEL_MAP:
            raise ValueError(f"Reservoir model '{storage_model_name}' not found for {self.id}")
        self.storage_model = RESERVOIR_MODEL_MAP[storage_model_name](params.get("parameters", {}))

        # --- State Variables ---
        self.storage_m3 = params.get("parameters", {}).get("initial_storage_m3", 0)
        self.inflow = 0.0  # m3/s
        self.outflow = 0.0 # m3/s

    def step(self, dt_hours, t_step_debug=None):
        """
        Performs a single simulation step for the reservoir.
        """
        # 1. First, update the storage with the inflow from the current time step.
        self.storage_m3 += self.inflow * dt_hours * 3600

        # 2. Now, calculate the outflow based on the updated storage.
        self.outflow = self.storage_model.calculate_outflow(self.storage_m3)

        # 3. Finally, update the storage by subtracting the outflow.
        self.storage_m3 -= self.outflow * dt_hours * 3600

        # Ensure storage doesn't go below zero
        self.storage_m3 = max(0, self.storage_m3)

        if self.id == "ReservoirA" and t_step_debug and t_step_debug % 30 == 0:
            print(f"[d:{t_step_debug}] ReservoirA Stats: In={self.inflow:.2f} m3/s, Out={self.outflow:.2f} m3/s, Storage={self.storage_m3 / 1e6:.2f} MCM")

        # 4. Reset inflow for next time step
        self.inflow = 0
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
                    params=params
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

        # Determine the number of steps from the first available sub-basin data
        first_subbasin_id = next((el["id"] for el in self.topology_data["elements"] if el["type"] == "sub_basin"), None)
        if not first_subbasin_id:
            raise ValueError("No sub-basins found in topology to determine simulation length.")
        num_steps = len(self.timeseries_data["data"][first_subbasin_id]["precipitation_mm"])

        results = {el_id: np.zeros(num_steps) for el_id in self.elements}

        for t in range(num_steps):
            for element_id in self.simulation_order:
                element = self.elements[element_id]

                # Default local_outflow is 0, important for reservoirs
                local_outflow = 0

                if isinstance(element, SubBasin):
                    precip = self.timeseries_data["data"][element_id]["precipitation_mm"][t]
                    evap = self.timeseries_data["data"][element_id]["evaporation_mm"][t]
                    outflow = element.step(precip, evap, dt_hours)
                elif isinstance(element, Reservoir):
                    outflow = element.step(dt_hours, t_step_debug=t)

                # Now, route this total flow through the reach to the next element
                if element_id in self.reaches:
                    reach = self.reaches[element_id]
                    routed_outflow = reach.route(outflow)

                    # Add the routed flow to the downstream element's inflow for the next step
                    downstream_element = self.elements[reach.to_id]
                    downstream_element.inflow += routed_outflow

                    results[element_id][t] = routed_outflow
                else:
                    # This is a sink node
                    results[element_id][t] = outflow

        return results
