# DemandAgent

## Function

A DemandAgent simulates water demand from consumers in the system. It publishes a value from a predefined time-series pattern at each simulation step.

## Parameters

| Key                   | Type          | Required | Description                                                                |
|-----------------------|---------------|----------|----------------------------------------------------------------------------|
| `consumption_pattern` | `list[float]` | Yes      | A list of numerical values representing the demand at each time step.      |
| `topic`               | `str`         | Yes      | The topic to publish the demand value to.                                  |

## Publishes To

- **Topic:** The value of the `topic` parameter.
- **Payload:**
  ```json
  {
    "value": <demand_float>
  }
  ```

## Subscribes To

This agent does not subscribe to any topics.
