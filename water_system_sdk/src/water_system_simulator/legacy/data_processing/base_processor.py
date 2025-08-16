from abc import ABC, abstractmethod

class BaseDataProcessor(ABC):
    """
    Abstract base class for all data processing strategies.
    """

    @abstractmethod
    def process(self, data_input: dict) -> dict:
        """
        Process the input data dictionary and return a processed dictionary.

        Args:
            data_input (dict): A dictionary containing data streams.

        Returns:
            dict: A dictionary containing the processed data.
        """
        pass
