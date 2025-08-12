class RegulatedReservoir:
    """
    A reservoir model with rule-based outflow based on storage levels.
    """
    def __init__(self, parameters):
        self.params = parameters
        self.max_storage_m3 = self.params.get("max_storage_m3", 1e8)
        self.min_outflow_m3s = self.params.get("min_outflow_m3s", 10)
        self.max_outflow_m3s = self.params.get("max_outflow_m3s", 500)

        # Define storage thresholds for different operational zones
        self.flood_control_level = 0.8 * self.max_storage_m3
        self.normal_level = 0.3 * self.max_storage_m3

    def calculate_outflow(self, available_storage_m3):
        """
        Calculates the outflow based on the total available water and a set of rules.

        Args:
            available_storage_m3 (float): The total volume of water available for release
                                         (storage from previous step + inflow from current step).

        Returns:
            float: The calculated outflow in m3/s.
        """
        outflow_m3s = 0

        # --- Spillage Logic (Priority 1) ---
        # If available water exceeds maximum capacity, the excess must be spilled.
        if available_storage_m3 > self.max_storage_m3:
            spillage_volume_m3 = available_storage_m3 - self.max_storage_m3
            # Convert spillage volume to an average flow rate over the time step
            spillage_flow_m3s = spillage_volume_m3 / (24 * 3600)
            outflow_m3s += spillage_flow_m3s
            # The remaining storage for regulation is the max capacity
            storage_for_regulation = self.max_storage_m3
        else:
            storage_for_regulation = available_storage_m3

        # --- Regulation Rules (Priority 2) ---
        regulated_outflow_m3s = 0
        if storage_for_regulation > self.flood_control_level:
            # Flood control operation: release a fraction of water above the normal level
            storage_above_normal = storage_for_regulation - self.normal_level
            release_fraction = 0.05 # Release 5% of storage above normal level
            regulated_outflow_m3s = (storage_above_normal * release_fraction) / (24 * 3600)

        elif storage_for_regulation > self.normal_level:
            # Normal operation: release a moderate amount
            storage_ratio = (storage_for_regulation - self.normal_level) / (self.flood_control_level - self.normal_level)
            regulated_outflow_m3s = self.min_outflow_m3s + storage_ratio * (self.max_outflow_m3s / 2 - self.min_outflow_m3s)

        else:
            # Conservation zone: release minimum environmental flow
            regulated_outflow_m3s = self.min_outflow_m3s

        # Total outflow is regulated + spillage
        outflow_m3s += regulated_outflow_m3s

        # Ensure outflow does not exceed physical limits or available water
        max_possible_outflow = available_storage_m3 / (24 * 3600)
        outflow_m3s = min(outflow_m3s, self.max_outflow_m3s, max_possible_outflow)

        return max(0, outflow_m3s)
