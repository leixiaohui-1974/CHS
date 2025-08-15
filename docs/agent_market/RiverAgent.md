# RiverAgent

## Function

A RiverAgent simulates a river system composed of multiple nodes and reaches using the 1D St. Venant equations. It can model complex hydrodynamic effects like backwater curves.

## Parameters

| Key               | Type   | Required | Description                                                                                                |
|-------------------|--------|----------|------------------------------------------------------------------------------------------------------------|
| `nodes_data`      | `list` | Yes      | A list of dictionaries, where each dictionary defines a node (e.g., its name, type, and properties).         |
| `reaches_data`    | `list` | Yes      | A list of dictionaries, where each dictionary defines a reach (e.g., its name, length, roughness, and geometry).|
| `state_topic`     | `str`  | Yes      | The topic to publish the full state of the river network to.                                               |
| `boundary_topics` | `dict` | Yes      | A dictionary mapping node names to the topics that provide their boundary conditions (e.g., inflow or level).|
| `solver_params`   | `dict` | No       | Optional parameters for the hydrodynamic solver.                                                           |

## Publishes To

- **Topic:** The value of the `state_topic` parameter.
- **Payload:** A complex dictionary representing the state of all nodes and reaches in the network.
  ```json
  {
    "nodes": {
      "node_1": {"level": 100.5, "flow": 50.2, ...},
      ...
    },
    "reaches": {
      "reach_1": {"flow_profile": [...], "area_profile": [...], ...},
      ...
    }
  }
  ```

## Subscribes To

- **Topics:** The topics specified as values in the `boundary_topics` dictionary.
- **Expected Payload:** The agent expects a payload with a `value` key for the boundary condition.
  - For an `InflowBoundary` node: `{"value": <inflow_float>}`
  - For a `LevelBoundary` node: `{"value": <level_float>}`
