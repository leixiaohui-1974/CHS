import uuid
from abc import ABC, abstractmethod
from .node import Node

class BaseStructure(ABC):
    """
    Abstract base class for a hydraulic structure connecting two nodes.
    A structure acts as an internal boundary condition.
    """
    def __init__(self, name: str, upstream_node: Node, downstream_node: Node, **kwargs):
        self.id = uuid.uuid4()
        self.name = name
        self.upstream_node = upstream_node
        self.downstream_node = downstream_node
        self.discharge = kwargs.get('discharge', 0.0)  # Initial discharge (m^3/s)

    @abstractmethod
    def add_to_matrix(self, A, B, var_map: dict, H_up: float, Q_s: float):
        """
        Adds the structure's governing equation and its derivatives to the
        global Jacobian matrix (A) and function vector (B).

        Args:
            A: The global Jacobian matrix (sparse).
            B: The global function vector.
            var_map: A dictionary to map entity IDs to their index in the matrix.
            H_up: Current water level at the upstream node.
            Q_s: Current discharge through this structure.
        """
        pass

    def __repr__(self):
        return (f"{self.__class__.__name__}(name='{self.name}', "
                f"from='{self.upstream_node.name}', to='{self.downstream_node.name}', "
                f"Q_struct={self.discharge:.2f} m^3/s)")


class WeirStructure(BaseStructure):
    """
    Represents a weir as an internal boundary condition.
    The weir equation provides a relationship between upstream water level and discharge.
    """
    def __init__(self, name: str, upstream_node: Node, downstream_node: Node, **kwargs):
        super().__init__(name, upstream_node, downstream_node, **kwargs)
        self.crest_elevation = kwargs.get('crest_elevation', 10.0)  # Weir crest elevation (m)
        self.weir_coefficient = kwargs.get('weir_coefficient', 1.7) # Broad-crested weir coefficient
        self.crest_width = kwargs.get('crest_width', 10.0) # Width of the weir crest (m)

    def add_to_matrix(self, A, B, var_map: dict, H_up: float, Q_s: float):
        """
        Adds the weir equation to the system:
        F(Q_s, H_up) = Q_s - Cw * b * (H_up - Z_crest)^(3/2) = 0
        This assumes free (unsubmerged) flow.
        """
        up_node_var_idx = var_map[self.upstream_node.id]
        struct_var_idx = var_map[self.id]

        # The row for this structure's equation corresponds to its variable index
        row_idx = struct_var_idx

        head_on_crest = H_up - self.crest_elevation

        if head_on_crest <= 0:
            # If water level is below crest, flow should be zero.
            # Equation: F(Q_s) = Q_s = 0
            B[row_idx] = Q_s
            A[row_idx, struct_var_idx] = 1.0 # dF/dQs = 1
        else:
            # Weir flow equation: F(Q_s, H_up) = ... = 0
            B[row_idx] = Q_s - self.weir_coefficient * self.crest_width * (head_on_crest ** 1.5)

            # Partial derivatives for Jacobian matrix
            # dF/dQs
            A[row_idx, struct_var_idx] = 1.0

            # dF/dH_up
            dF_dHup = -1.5 * self.weir_coefficient * self.crest_width * (head_on_crest ** 0.5)
            A[row_idx, up_node_var_idx] = dF_dHup
