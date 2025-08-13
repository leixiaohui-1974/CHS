import uuid
import numpy as np
from .node import Node

class Reach:
    """
    Represents a river or channel segment (a pipe) in the hydrodynamic network.
    """
    def __init__(self, name: str, upstream_node: Node, downstream_node: Node, **kwargs):
        self.id = uuid.uuid4()
        self.name = name
        self.upstream_node = upstream_node
        self.downstream_node = downstream_node
        self.length = kwargs.get('length', 1000.0)  # Length of the reach (m)
        self.manning_coefficient = kwargs.get('manning_coefficient', 0.03)  # Manning's roughness coefficient
        self.bed_slope = kwargs.get('bed_slope', 0.0)  # Bed slope of the reach
        self.discharge = kwargs.get('discharge', 0.0)  # Initial discharge (m^3/s)

        # Cross-section properties for trapezoidal channel
        self.bottom_width = kwargs.get('bottom_width', 10.0)  # Bottom width of the channel (m)
        self.side_slope = kwargs.get('side_slope', 0.0)  # Side slope (z for zH:1V), 0 for rectangular

    def __repr__(self):
        return (f"{self.__class__.__name__}(name='{self.name}', "
                f"from='{self.upstream_node.name}', to='{self.downstream_node.name}', "
                f"Q={self.discharge:.2f} m^3/s)")

    def get_area(self, water_depth: float) -> float:
        """Calculates the cross-sectional area for a given water depth."""
        if water_depth < 0: return 0
        return (self.bottom_width + self.side_slope * water_depth) * water_depth

    def get_wetted_perimeter(self, water_depth: float) -> float:
        """Calculates the wetted perimeter for a given water depth."""
        if water_depth < 0: return 0
        return self.bottom_width + 2 * water_depth * np.sqrt(1 + self.side_slope**2)

    def get_hydraulic_radius(self, water_depth: float) -> float:
        """Calculates the hydraulic radius for a given water depth."""
        if water_depth < 0: return 0
        area = self.get_area(water_depth)
        perimeter = self.get_wetted_perimeter(water_depth)
        return area / perimeter if perimeter > 0 else 0.0

    def get_top_width(self, water_depth: float) -> float:
        """Calculates the top width for a given water depth."""
        if water_depth < 0: return 0
        return self.bottom_width + 2 * self.side_slope * water_depth
