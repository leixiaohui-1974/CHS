from pydantic import BaseModel, Field
from typing import Any
import time

class Message(BaseModel):
    """
    Represents a message passed between agents in the system.
    """
    topic: str
    sender_id: str
    timestamp: float = Field(default_factory=time.time)
    payload: Any
