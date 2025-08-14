from .base_agent import BaseEmbodiedAgent

class SensingEmbodiedAgent(BaseEmbodiedAgent):
    """
    Represents a "sensory and cognitive" system for an observable object
    like a river reach, reservoir, or pipeline.

    Its core responsibility is to handle data acquisition, processing,
    fusion, state evaluation, and forecasting. It provides a clear,
    processed picture of the state of the object it is observing.
    """
    def step(self, dt: float, **kwargs):
        """
        Executes the sensing and data processing logic for one time step.
        """
        # Placeholder for sensing logic (e.g., data cleaning, fusion).
        # This will be implemented in concrete subclasses.
        print(f"INFO: SensingEmbodiedAgent {self.name} is stepping.")
        pass
