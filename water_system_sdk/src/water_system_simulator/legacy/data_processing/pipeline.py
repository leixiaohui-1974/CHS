from typing import List
from .base_processor import BaseDataProcessor

class DataProcessingPipeline:
    """
    Manages a sequence of data processing steps.
    """
    def __init__(self, processors: List[BaseDataProcessor]):
        """
        Initializes the pipeline with a list of processor objects.

        Args:
            processors (List[BaseDataProcessor]): A list of data processor instances.
        """
        self.processors = processors

    def process(self, data_input: dict) -> dict:
        """
        Processes data by passing it through the entire pipeline.

        Args:
            data_input (dict): The initial raw data dictionary.

        Returns:
            dict: The processed data dictionary.
        """
        processed_data = data_input
        for processor in self.processors:
            processed_data = processor.process(processed_data)
        return processed_data
