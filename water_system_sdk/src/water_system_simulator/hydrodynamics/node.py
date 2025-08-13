import uuid

class Node:
    """
    Base class for a node in the hydrodynamic network.
    """
    def __init__(self, name: str, **kwargs):
        self.id = uuid.uuid4()
        self.name = name
        self.head = kwargs.get('head', 0.0)  # Water surface elevation (m)
        self.bed_elevation = kwargs.get('bed_elevation', 0.0) # Bed elevation (m)

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', head={self.head:.2f}, z={self.bed_elevation:.2f})"


class JunctionNode(Node):
    """
    Represents a simple connection point where multiple reaches meet.
    """
    def __init__(self, name: str, **kwargs):
        super().__init__(name, **kwargs)


class BoundaryNode(Node):
    """
    Base class for boundary condition nodes.
    """
    def __init__(self, name: str, **kwargs):
        super().__init__(name, **kwargs)


class InflowBoundary(BoundaryNode):
    """
    Represents an upstream boundary with a specified inflow.
    """
    def __init__(self, name: str, inflow: float, **kwargs):
        super().__init__(name, **kwargs)
        self.inflow = inflow  # Inflow discharge (m^3/s)

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', inflow={self.inflow:.2f})"


class LevelBoundary(BoundaryNode):
    """
    Represents a downstream boundary with a specified water level.
    """
    def __init__(self, name: str, level: float, **kwargs):
        super().__init__(name, **kwargs)
        self.level = level  # Water level (m)

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', level={self.level:.2f})"
