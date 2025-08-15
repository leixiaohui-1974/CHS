# GateAgent

## Function

A GateAgent simulates a controllable gate in a channel or reservoir, calculating the flow of water through it based on upstream/downstream water levels and the gate's opening.

## Parameters

| Key               | Type    | Required | Description                                                    |
|-------------------|---------|----------|----------------------------------------------------------------|
| `num_gates`       | `int`   | Yes      | The number of identical gates at the structure.                |
| `gate_width`      | `float` | Yes      | The width of a single gate in meters.                          |
| `discharge_coeff` | `float` | Yes      | The discharge coefficient of the gate.                         |
| `upstream_topic`  | `str`   | Yes      | The topic to subscribe to for the upstream water level.        |
| `downstream_topic`| `str`   | Yes      | The topic to subscribe to for the downstream water level.      |
| `opening_topic`   | `str`   | Yes      | The topic to subscribe to for the gate opening command.        |
| `state_topic`     | `str`   | Yes      | The topic to publish the gate's state to.                      |

## Publishes To

- **Topic:** The value of the `state_topic` parameter.
- **Payload:**
  ```json
  {
    "flow": <flow_rate_float>
  }
  ```

## Subscribes To

1.  **Upstream Level:** The value of the `upstream_topic` parameter.
    - **Expected Payload:** `{"level": <level_float>}` or `{"output": <level_float>}`
2.  **Downstream Level:** The value of the `downstream_topic` parameter.
    - **Expected Payload:** `{"level": <level_float>}` or `{"output": <level_float>}`
3.  **Gate Opening:** The value of the `opening_topic` parameter.
    - **Expected Payload:** `{"value": <opening_float>}` where opening is a value from 0.0 to 1.0.
