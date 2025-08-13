import yaml
import csv
from typing import Dict, List, Any

def parse_topology(file_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Parses the YAML system topology file.

    Args:
        file_path (str): The path to the topology.yml file.

    Returns:
        Dict[str, List[Dict[str, Any]]]: A dictionary containing the parsed component data.
    """
    try:
        with open(file_path, 'r') as f:
            config = yaml.safe_load(f)
        # Basic validation
        if 'components' not in config or not isinstance(config['components'], list):
            raise ValueError("Topology file must contain a 'components' list.")
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Topology file not found at: {file_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file: {e}")

def parse_disturbances(file_path: str) -> List[Dict[str, float]]:
    """
    Parses the CSV disturbance file.

    Args:
        file_path (str): The path to the disturbances.csv file.

    Returns:
        List[Dict[str, float]]: A list of dictionaries, where each dictionary
                                represents a row with headers as keys.
    """
    try:
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            # Convert string values to floats
            disturbances = [{k: float(v) for k, v in row.items()} for row in reader]
        return disturbances
    except FileNotFoundError:
        # It's okay if the disturbance file doesn't exist; it's optional.
        return []
    except Exception as e:
        raise ValueError(f"Error parsing CSV file: {e}")
