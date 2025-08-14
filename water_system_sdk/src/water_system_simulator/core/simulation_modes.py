from enum import Enum, auto

class SimulationMode(Enum):
    """
    Enumeration for the different simulation fidelity modes.
    """
    STEADY = auto()
    DYNAMIC = auto()
    PRECISION = auto() # Note: The user referred to this as TRANSIENT and PRECISION. Using PRECISION for the enum member name.
