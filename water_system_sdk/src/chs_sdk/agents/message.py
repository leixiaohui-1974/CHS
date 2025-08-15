from pydantic import BaseModel, Field
from typing import Any, Optional
import time

class Message(BaseModel):
    """
    Represents a message passed between agents in the system.
    """
    topic: str
    sender_id: str
    timestamp: float = Field(default_factory=time.time)
    payload: Any

class MeasurementPayload(BaseModel):
    """
    Defines the structure for a measurement data payload.
    This provides a standardized format for sensor readings and other
    real-world observations used in data assimilation.
    """
    value: float
    quality: Optional[str] = 'good'
    timestamp: float = Field(default_factory=time.time)
