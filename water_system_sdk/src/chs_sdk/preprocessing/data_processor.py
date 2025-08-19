from abc import ABC, abstractmethod
import pandas as pd


class BaseDataProcessor(ABC):
    """
    Abstract base class for all data processing components.
    """
    @abstractmethod
    def process(self, data_input: pd.DataFrame) -> pd.DataFrame:
        """
        Process the input data and return the processed data.

        Args:
            data_input (pd.DataFrame): The input data to process.

        Returns:
            pd.DataFrame: The processed data.
        """
        pass


class Pipeline(BaseDataProcessor):
    """
    A pipeline that chains multiple data processors together.
    """
    def __init__(self, processors: list):
        """
        Initializes the Pipeline.

        Args:
            processors (list): A list of data processor instances that inherit
                               from BaseDataProcessor.
        """
        self.processors = processors

    def process(self, data_input: pd.DataFrame) -> pd.DataFrame:
        """
        Processes the data by passing it through each processor in the pipeline.
        """
        data = data_input
        for processor in self.processors:
            data = processor.process(data)
        return data


class DataCleaner(BaseDataProcessor):
    """
    A data processor to clean data, e.g., by filling missing values.
    """
    def __init__(self, strategy: str = 'ffill', value=None):
        """
        Initializes the DataCleaner.

        Args:
            strategy (str): The strategy for filling missing values.
                            Options: 'ffill', 'bfill', 'mean', 'median', 'constant'.
            value (scalar, optional): The value to use when strategy is 'constant'.
        """
        self.strategy = strategy
        self.value = value

    def process(self, data_input: pd.DataFrame) -> pd.DataFrame:
        """
        Fills missing values in the DataFrame.
        """
        if self.strategy == 'ffill':
            return data_input.ffill()
        elif self.strategy == 'bfill':
            return data_input.bfill()
        elif self.strategy == 'mean':
            return data_input.fillna(data_input.mean())
        elif self.strategy == 'median':
            return data_input.fillna(data_input.median())
        elif self.strategy == 'constant':
            return data_input.fillna(self.value)
        else:
            raise ValueError(f"Unknown cleaning strategy: {self.strategy}")


class UnitConverter(BaseDataProcessor):
    """
    A data processor to convert units by applying a scaling factor.
    """
    def __init__(self, scale_factor: float, columns: list = None):
        """
        Initializes the UnitConverter.

        Args:
            scale_factor (float): The factor to multiply the data by.
            columns (list, optional): A list of column names to apply the
                                      conversion to. If None, applies to all
                                      numeric columns. Defaults to None.
        """
        self.scale_factor = scale_factor
        self.columns = columns

    def process(self, data_input: pd.DataFrame) -> pd.DataFrame:
        """
        Applies the unit conversion.
        """
        data = data_input.copy()
        if self.columns:
            for col in self.columns:
                if col in data.columns and pd.api.types.is_numeric_dtype(data[col]):
                    data[col] = data[col] * self.scale_factor
        else:
            for col in data.columns:
                if pd.api.types.is_numeric_dtype(data[col]):
                    data[col] = data[col] * self.scale_factor
        return data


class TimeResampler(BaseDataProcessor):
    """
    A data processor to resample time series data to a different frequency.
    """
    def __init__(self, rule: str, agg_func: str = 'mean'):
        """
        Initializes the TimeResampler.

        Args:
            rule (str): The new frequency (e.g., 'D' for daily, 'H' for hourly).
                        See pandas documentation for frequency strings.
            agg_func (str): The aggregation function to use (e.g., 'mean', 'sum').
        """
        self.rule = rule
        self.agg_func = agg_func

    def process(self, data_input: pd.DataFrame) -> pd.DataFrame:
        """
        Resamples the time series data.
        """
        if not isinstance(data_input.index, pd.DatetimeIndex):
            raise TypeError("TimeResampler requires a DatetimeIndex.")
        return data_input.resample(self.rule).agg(self.agg_func)
