from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseWorkflow(ABC):
    """
    Abstract base class for all workflows.
    """

    @abstractmethod
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the workflow.

        :param context: A dictionary containing all necessary data and parameters
                        for the workflow to run.
        :return: A dictionary containing the results of the workflow.
        """
        pass
