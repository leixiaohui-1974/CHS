from .base_agent import BaseEmbodiedAgent
from chs_sdk.agents.message import Message
from chs_sdk.workflows.system_id_workflow import SystemIDWorkflow
import numpy as np

class PerceptionAgent(BaseEmbodiedAgent):
    """
    Represents a "sensory and cognitive" system for an observable object
    like a river reach, reservoir, or pipeline.

    Its core responsibility is to handle data acquisition, processing,
    fusion, state evaluation, and forecasting. It provides a clear,
    processed picture of the state of the object it is observing.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.latest_model_parameters = None
        self.latest_forecast = None
        self.active_alarms = []

    def on_message(self, message: Message):
        """
        Handles incoming data messages, processing them through the pipeline.
        """
        if self.processing_pipeline:
            processed_data = self.processing_pipeline.run(message.payload)
            return processed_data
        return message.payload

    def execute_offline_identification(self, data, strategy='steady_state'):
        """
        Executes an offline system identification task.
        """
        workflow = SystemIDWorkflow()
        # This is a simplified call; a real implementation would need more context
        context = {
            'data': data,
            'model_type': strategy,
            'dt': 1,
            'initial_guess': [0.1, 0.1],
            'bounds': [(0, 1), (0, 1)]
        }
        result = workflow.run(context)
        self.latest_model_parameters = result.get("identified_parameters")
        return self.latest_model_parameters

    def execute_online_identification(self, new_data_point):
        """
        Executes an online system identification update (placeholder).
        """
        # In a real implementation, this would call an RLS or EKF estimator.
        # For now, we'll simulate a small update.
        if self.latest_model_parameters is None:
            self.latest_model_parameters = np.array([0.5, 0.5])

        # Simulate a small random walk for the parameters
        self.latest_model_parameters += (np.random.rand(2) - 0.5) * 0.05
        return self.latest_model_parameters

    def step(self, dt: float, **kwargs):
        """
        The main execution loop for the PerceptionAgent.
        In a real scenario, this would be driven by a scheduler or new data.
        """
        # 1. Process incoming data (if any)
        # This part would be integrated with a message bus in a full system

        # 2. Run online identification (if enabled)
        # new_data = get_new_data() # Placeholder for data acquisition
        # self.execute_online_identification(new_data)

        # 3. Generate predictions
        # self.update_forecast()

        # 4. Check for alarms
        # self.check_alarms()

        # 5. Publish situational awareness message
        # self.publish_awareness_message()

        print(f"INFO: PerceptionAgent {self.name} is stepping.")
        pass

    def publish_awareness_message(self):
        """
        Publishes a comprehensive situational awareness message.
        """
        payload = {
            "cleaned_value": "some_value", # from processing pipeline
            "model_parameters": self.latest_model_parameters,
            "forecast": self.latest_forecast,
            "alarms": self.active_alarms
        }
        message = Message(
            topic=f"agent.{self.name}.awareness",
            sender_id=self.name,
            payload=payload
        )
        # In a real system, this would be put on a message bus
        print(f"DEBUG: Publishing awareness message: {message.json()}")
        return message
