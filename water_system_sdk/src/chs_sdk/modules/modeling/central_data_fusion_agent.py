from .base_model import BaseModel
from chs_sdk.modules.data_processing.pipeline import DataProcessingPipeline

class CentralDataFusionAgent(BaseModel):
    """
    An agent responsible for fusing data from multiple sources.
    """
    def __init__(self, pipeline: DataProcessingPipeline, **kwargs):
        """
        Initializes the CentralDataFusionAgent.

        Args:
            pipeline (DataProcessingPipeline): The data processing and fusion pipeline.
        """
        super().__init__(**kwargs)
        if pipeline is None:
            raise ValueError("CentralDataFusionAgent requires a data processing pipeline.")
        self.data_pipeline = pipeline
        self.state = {'fused_data': {}}
        self.output = self.state['fused_data']

    def step(self, **kwargs):
        """
        Processes incoming data from multiple sources using its internal pipeline.
        It expects keyword arguments where each key is a data source name
        and the value is the data from that source.

        Example:
            step(source_A={'pressure': 2.5}, source_B={'pressure': 2.6})

        The internal pipeline is expected to handle this structure.
        For instance, a DataFusionEngine will fuse these inputs.
        """
        # We can directly pass the kwargs dictionary to the pipeline,
        # as it represents the multiple data streams to be processed.
        processed_data = self.data_pipeline.process(kwargs)
        self.state['fused_data'] = processed_data
        self.output = self.state['fused_data']
        return self.output

    def get_state(self) -> dict:
        """
        Returns the current state of the agent (the fused data).
        """
        return self.state
