import numpy as np
from .base_model import BaseModel

class ChannelCrossSection:
    """Helper class to manage channel geometry."""
    def __init__(self, shape_type: str, **params):
        self.shape_type = shape_type.lower()
        self.params = params
        if self.shape_type == 'trapezoid':
            self.bottom_width = params['bottom_width']
            self.side_slope = params['side_slope'] # z where slope is zH:1V
        else:
            raise NotImplementedError(f"Shape type '{self.shape_type}' not supported.")

    def area(self, y): # y is depth
        y = max(0, y)
        if self.shape_type == 'trapezoid':
            return (self.bottom_width + self.side_slope * y) * y

    def wetted_perimeter(self, y):
        y = max(0, y)
        if self.shape_type == 'trapezoid':
            return self.bottom_width + 2 * y * np.sqrt(1 + self.side_slope**2)

    def hydraulic_radius(self, y):
        y = max(0, y)
        area = self.area(y)
        if area <= 1e-6: return 0
        return area / self.wetted_perimeter(y)

    def top_width(self, y):
        y = max(0, y)
        if self.shape_type == 'trapezoid':
            return self.bottom_width + 2 * self.side_slope * y
        return 0

class ChannelModel(BaseModel):
    """
    Represents a channel reach using the kinematic wave approximation of the
    St. Venant equations, with Manning's equation for friction.
    Also simulates advection-dispersion of a conservative tracer.
    """
    def __init__(self,
                 length: float,
                 num_cells: int,
                 cross_section: dict, # e.g., {'type': 'trapezoid', 'bottom_width': 10, 'side_slope': 2}
                 manning_n: float,
                 bed_slope: float,
                 initial_depth: float = 0.1,
                 initial_concentration: float = 0.0,
                 dispersion_coeff: float = 0.0, # Longitudinal dispersion coefficient
                 **kwargs):
        super().__init__(**kwargs)
        self.length = length
        self.num_cells = num_cells
        self.cell_length = length / num_cells
        self.manning_n = manning_n
        self.bed_slope = max(1e-6, bed_slope) # Avoid zero slope
        self.dispersion_coeff = dispersion_coeff

        self.cross_section = ChannelCrossSection(**cross_section)

        # State variables
        self.depths = np.full(num_cells, initial_depth)
        self.flows = np.zeros(num_cells)
        self.concentrations = np.full(num_cells, initial_concentration)

        self._update_flows_from_depths()
        self.output = self.flows[-1] # Outlet flow

    def _update_flows_from_depths(self):
        """Update flow in each cell based on its depth using Manning's Eq."""
        for i in range(self.num_cells):
            y = self.depths[i]
            if y <= 0:
                self.flows[i] = 0
                continue

            area = self.cross_section.area(y)
            rh = self.cross_section.hydraulic_radius(y)
            # Manning's Equation: Q = (1/n) * A * R_h^(2/3) * S^(1/2)
            self.flows[i] = (1.0 / self.manning_n) * area * (rh**(2/3)) * np.sqrt(self.bed_slope)

    def step(self, dt: float, upstream_flow: float, upstream_concentration: float = 0.0, **kwargs):
        """
        Performs a single hydraulic and quality step.
        """
        # Hydraulic step (kinematic wave)
        self._update_flows_from_depths()
        new_depths = np.copy(self.depths)
        for i in range(self.num_cells):
            q_in = self.flows[i-1] if i > 0 else upstream_flow
            q_out = self.flows[i]

            area = self.cross_section.area(self.depths[i])
            delta_area = (q_in - q_out) * (dt / self.cell_length)

            top_width = self.cross_section.top_width(self.depths[i])
            if top_width > 1e-6:
                delta_y = delta_area / top_width
                new_depths[i] += delta_y
        self.depths = np.maximum(0, new_depths)

        # Quality step (advection-dispersion)
        self.update_quality(dt, upstream_concentration)

        # Final update of flows and output
        self._update_flows_from_depths()
        self.output = self.flows[-1]
        return self.output

    def update_quality(self, dt: float, upstream_concentration: float):
        """
        Performs a quality step using an advection-dispersion equation.
        """
        new_concentrations = np.copy(self.concentrations)
        # CFL condition check (simple version)
        velocities = self.flows / np.array([self.cross_section.area(y) if self.cross_section.area(y) > 1e-6 else 1 for y in self.depths])
        max_v = np.max(np.abs(velocities))
        if max_v > 0 and dt > self.cell_length / max_v:
            # Potentially unstable, but we proceed for this simple model
            pass

        for i in range(self.num_cells):
            area = self.cross_section.area(self.depths[i])
            v = self.flows[i] / area if area > 1e-6 else 0

            # Advection term (upwind scheme)
            c_prev = self.concentrations[i-1] if i > 0 else upstream_concentration
            advection = -v * (self.concentrations[i] - c_prev) / self.cell_length

            # Dispersion term (central difference)
            c_next = self.concentrations[i+1] if i < self.num_cells - 1 else self.concentrations[i]
            dispersion = self.dispersion_coeff * (c_prev - 2*self.concentrations[i] + c_next) / self.cell_length**2

            new_concentrations[i] += (advection + dispersion) * dt

        self.concentrations = np.maximum(0, new_concentrations)

    def get_state(self):
        return {
            "depth_profile": self.depths.tolist(),
            "flow_profile": self.flows.tolist(),
            "concentration_profile": self.concentrations.tolist(),
            "outlet_flow": self.flows[-1],
            "outlet_concentration": self.concentrations[-1]
        }
