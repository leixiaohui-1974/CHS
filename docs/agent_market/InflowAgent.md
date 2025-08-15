# InflowAgent

## Function

An InflowAgent simulates an external inflow into the system, such as rainfall or a river feed. It publishes a value from a predefined time-series pattern at each simulation step.

## Parameters

| Key                | Type          | Required | Description                                                                |
|--------------------|---------------|----------|----------------------------------------------------------------------------|
| `rainfall_pattern` | `list[float]` | Yes      | A list of numerical values representing the inflow at each time step.      |
| `topic`            | `str`         | Yes      | The topic to publish the inflow value to.                                  |

## Publishes To

- **Topic:** The value of the `topic` parameter.
- **Payload:**
  ```json
  {
    "value": <inflow_float>
  }
  ```

## Subscribes To

This agent does not subscribe to any topics.
