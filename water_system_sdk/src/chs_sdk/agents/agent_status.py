from enum import Enum, auto


class AgentStatus(Enum):
    """
    Represents the lifecycle status of an agent.
    """
    #: The agent has been created but not yet started.
    INITIALIZING = auto()
    #: The agent is running normally.
    RUNNING = auto()
    #: The agent has been stopped by a user or the system.
    STOPPED = auto()
    #: The agent has encountered an unrecoverable error.
    FAULT = auto()
    #: The agent is in the process of shutting down.
    SHUTTING_DOWN = auto()
