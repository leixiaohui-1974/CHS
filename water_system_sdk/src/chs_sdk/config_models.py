from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class SimulationParams(BaseModel):
    """Pydantic model for simulation parameters."""
    total_time: float = Field(..., description="Total simulation time.")
    dt: float = Field(..., description="Time step for the simulation.")

class Connection(BaseModel):
    """Pydantic model for a connection between components."""
    source: str
    target: str

class Component(BaseModel):
    """A generic Pydantic model for a simulation component."""
    type: str
    properties: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, Any]] = None # Allow both 'properties' and 'params'

    # Note: A more advanced implementation would use a discriminated union
    # to validate the params for each component type. For now, this provides
    # basic structure validation.

class TopLevelConfig(BaseModel):
    """The root Pydantic model for the entire simulation configuration."""
    simulation_params: SimulationParams
    components: Dict[str, Component]
    connections: Optional[List[Connection]] = []
    execution_order: List[Any] # Can be str or dict, so kept as Any for now
    preprocessing: Optional[List[str]] = []
    logger_config: Optional[List[str]] = []
    events: Optional[List[Dict[str, Any]]] = []
    datasets: Optional[Dict[str, Any]] = {}
    logging: Optional[Dict[str, Any]] = {}
