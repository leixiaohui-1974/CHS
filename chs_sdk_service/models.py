from pydantic import BaseModel, Field
from typing import List, Dict, Any, Tuple

# ======================================================================================
# Core Models for Simulation and Control
# ======================================================================================

class SystemModel(BaseModel):
    """
    Defines the parameters for a system model, specifically for a TankAgent,
    which is a common use case in this SDK.
    """
    area: float = Field(..., example=100.0, description="The cross-sectional area of the tank.")
    initial_level: float = Field(default=0.0, example=5.0, description="The initial water level in the tank.")
    max_level: float = Field(default=20.0, example=20.0, description="The maximum water level of the tank.")

class ControllerConfig(BaseModel):
    """
    Defines the parameters for a PID controller.
    """
    Kp: float = Field(..., example=0.5)
    Ki: float = Field(..., example=0.1)
    Kd: float = Field(..., example=0.01)

# ======================================================================================
# Models for the /run_simulation Endpoint
# ======================================================================================

class AgentConfig(BaseModel):
    """
    Represents the configuration for a single agent in the agent society.
    This is a flexible model to accommodate different agent types.
    """
    id: str = Field(..., example="main_tank")
    # The original config uses 'class', which is a reserved keyword.
    # Pydantic's alias feature handles this perfectly.
    class_path: str = Field(..., alias="class", example="chs_sdk.agents.body_agents.TankAgent")
    params: Dict[str, Any] = Field(default_factory=dict, example={"area": 150.0, "initial_level": 4.5})

class SimulationSettings(BaseModel):
    """
    Defines the settings for a simulation run.
    """
    duration: int = Field(..., example=100, description="Total simulation duration in seconds.")
    time_step: float = Field(default=1.0, example=1.0, description="Time step for the simulation in seconds.")

class ScenarioConfig(BaseModel):
    """
    Represents a full simulation scenario configuration, used as the
    request body for the /api/v1/run_simulation endpoint.
    """
    simulation_settings: SimulationSettings
    agent_society: List[AgentConfig]

# ======================================================================================
# Models for the /run_workflow Endpoint
# ======================================================================================

class TimeSeriesDataRow(BaseModel):
    """
    A single row of time-series data for system identification.
    """
    inflow: float
    outflow: float

class SystemIdWorkflowContext(BaseModel):
    """
    Request body for the 'system_id_workflow'.
    """
    data: List[TimeSeriesDataRow]
    model_type: str = Field(..., example="Muskingum", description="The type of model to identify.")
    dt: float = Field(..., example=1.0, description="The time step of the provided data.")
    initial_guess: List[float] = Field(..., example=[10.0, 0.2], description="Initial guess for model parameters.")
    bounds: Tuple[List[float], List[float]] = Field(..., example=([0, 0], [100, 0.5]), description="Bounds for parameter optimization, in the format ([min_bounds], [max_bounds]).")

class SystemModelAgentConfig(BaseModel):
    """
    A specific agent configuration for the system to be controlled in the tuning workflow.
    """
    class_path: str = Field(alias="class", default="chs_sdk.agents.body_agents.TankAgent")
    params: SystemModel

class ControlTuningWorkflowContext(BaseModel):
    """
    Request body for the 'control_tuning_workflow'.
    """
    system_model: Dict[str, Any] = Field(..., example={'params': {'area': 100.0, 'initial_level': 5.0, 'max_level': 20.0}}, description="Configuration of the system agent to be controlled.")
    optimization_objective: str = Field(..., example="ISE", description="The objective function to minimize (e.g., 'ISE', 'IAE').")
    parameter_bounds: List[Tuple[float, float]] = Field(..., example=[(0, 10), (0, 5), (0, 1)], description="Bounds for each PID parameter [Kp, Ki, Kd].")
    initial_guess: List[float] = Field(..., example=[0.5, 0.1, 0.01], description="Initial guess for the PID parameters.")
