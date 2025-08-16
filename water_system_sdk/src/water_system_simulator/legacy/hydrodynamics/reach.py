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
        if water_depth < 0: return 0.0
        return float((self.bottom_width + self.side_slope * water_depth) * water_depth)

    def get_wetted_perimeter(self, water_depth: float) -> float:
        """Calculates the wetted perimeter for a given water depth."""
        if water_depth < 0: return 0.0
        return float(self.bottom_width + 2 * water_depth * np.sqrt(1 + self.side_slope**2))

    def get_hydraulic_radius(self, water_depth: float) -> float:
        """Calculates the hydraulic radius for a given water depth."""
        if water_depth < 0: return 0.0
        area = self.get_area(water_depth)
        perimeter = self.get_wetted_perimeter(water_depth)
        return float(area / perimeter) if perimeter > 0 else 0.0

    def get_top_width(self, water_depth: float) -> float:
        """Calculates the top width for a given water depth."""
        if water_depth < 0: return 0.0
        return float(self.bottom_width + 2 * self.side_slope * water_depth)

    def get_critical_depth(self, discharge: float, g: float = 9.81, tolerance=1e-6, max_iter=20) -> float:
        """
        Calculates the critical depth for a given discharge using Newton-Raphson method.
        Solves the equation: Q^2 / g = A^3 / T
        """
        if abs(discharge) < 1e-6:
            return 0.0

        # Initial guess using the formula for a wide rectangular channel
        y_crit = (discharge**2 / (self.bottom_width**2 * g))**(1/3)

        for _ in range(max_iter):
            A = self.get_area(y_crit)
            T = self.get_top_width(y_crit)

            if A < 1e-6 or T < 1e-6: # Avoid division by zero
                return float(y_crit)

            f = A**3 / T - discharge**2 / g

            # Derivative of f(y) w.r.t y
            dA_dy = T
            dT_dy = 2 * self.side_slope
            df_dy = (3 * A**2 * dA_dy * T - A**3 * dT_dy) / T**2

            if abs(df_dy) < 1e-6:
                break # Avoid division by zero, solution converged

            y_new = y_crit - f / df_dy

            if abs(y_new - y_crit) < tolerance:
                return float(y_new)
            y_crit = y_new

        return float(y_crit) # Return best guess if not converged

    def get_froude_number(self, water_depth: float, discharge: float, g: float = 9.81) -> float:
        """Calculates the Froude number for a given water depth and discharge."""
        if water_depth <= 1e-6:
            return 0.0

        area = self.get_area(water_depth)
        if area <= 1e-6:
            return 0.0

        top_width = self.get_top_width(water_depth)
        hydraulic_depth = area / top_width
        velocity = discharge / area

        froude = velocity / np.sqrt(g * hydraulic_depth)
        return float(froude)
