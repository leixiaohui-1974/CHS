from .base_agent import BaseAgent
from .message import Message
from water_system_sdk.src.water_system_simulator.disturbances.disturbance_models import WaterConsumptionModel, RainfallModel


class DemandAgent(BaseAgent):
    """
    An agent that simulates water demand based on a predefined pattern.
    """
    def __init__(self, agent_id, kernel, consumption_pattern, topic):
        super().__init__(agent_id, kernel)
        self.model = WaterConsumptionModel(consumption_pattern)
        self.topic = topic
        self.time_step = 0

    def execute(self, current_time: float):
        """
        Publishes the next demand value from the consumption pattern.
        """
        demand = self.model.get_consumption(self.time_step)
        self._publish(self.topic, {"value": demand})
        self.time_step += 1

    def on_message(self, message: Message):
        """
        This agent does not subscribe to any topics.
        """
        pass


class InflowAgent(BaseAgent):
    """
    An agent that simulates inflow (e.g., rainfall) based on a data pattern,
    which can be provided as a list or from a CSV file.
    """
    def __init__(self, agent_id, kernel, topic, rainfall_pattern=None, rainfall_file=None, **kwargs):
        """
        Initializes the InflowAgent.

        Args:
            topic (str): The topic to publish the inflow data to.
            rainfall_pattern (list, optional): A list of inflow values.
            rainfall_file (str, optional): Path to a CSV file with inflow data.
        """
        super().__init__(agent_id, kernel, **kwargs)
        self.model = RainfallModel(rainfall_pattern=rainfall_pattern, rainfall_file=rainfall_file)
        self.topic = topic
        self.time_step = 0

    def execute(self, current_time: float):
        """
        Publishes the next inflow value from the model.
        """
        inflow = self.model.get_rainfall(self.time_step)
        self._publish(self.topic, {"value": inflow})
        self.time_step += 1

    def on_message(self, message: Message):
        """
        This agent does not subscribe to any topics.
        """
        pass
