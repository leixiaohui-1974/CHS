import json

def load_topology_from_json(filepath):
    """
    Loads basin topology from a JSON file.

    Args:
        filepath (str): The path to the topology JSON file.

    Returns:
        dict: The loaded topology data.
    """
    with open(filepath, 'r') as f:
        topology = json.load(f)
    # Basic validation could be added here
    return topology

def load_timeseries_from_json(filepath):
    """
    Loads time series data from a JSON file.

    Args:
        filepath (str): The path to the time series JSON file.

    Returns:
        dict: The loaded time series data.
    """
    with open(filepath, 'r') as f:
        timeseries = json.load(f)
    # Basic validation could be added here
    return timeseries

def load_parameters_from_json(filepath):
    """
    Loads model parameters from a JSON file.

    Args:
        filepath (str): The path to the parameters JSON file.

    Returns:
        dict: The loaded parameters data.
    """
    with open(filepath, 'r') as f:
        parameters = json.load(f)
    # Basic validation could be added here
    return parameters
