from .base_model import BaseModel
from chs_sdk.modules.data_processing.pipeline import DataProcessingPipeline

class PumpStationAgent(BaseModel):
    """
    Represents a pump station that processes local sensor data.
    """
    def __init__(self, pipeline: DataProcessingPipeline = None, **kwargs):
        """
        Initializes the PumpStationAgent.

        Args:
            pipeline (DataProcessingPipeline, optional): A data processing pipeline
                                                         for cleaning/fusing local sensor data.
        """
        super().__init__(**kwargs)
        self.data_pipeline = pipeline
        self.state = {'processed_data': {}}
        self.output = self.state['processed_data']

    def step(self, raw_sensor_input: dict, **kwargs):
        """
        Processes incoming sensor data using its internal pipeline.

        Args:
            raw_sensor_input (dict): A dictionary of raw sensor readings.
        """
        if self.data_pipeline:
            processed_data = self.data_pipeline.process(raw_sensor_input)
            self.state['processed_data'] = processed_data
        else:
            # If no pipeline, just store the raw data
            self.state['processed_data'] = raw_sensor_input

        self.output = self.state['processed_data']
        return self.output

    def get_state(self) -> dict:
        """
        Returns the current state of the agent (the processed data).
        """
        return self.state
