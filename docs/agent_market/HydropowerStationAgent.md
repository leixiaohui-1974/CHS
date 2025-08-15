# HydropowerStationAgent

## Function

A HydropowerStationAgent simulates a hydropower generation facility. It calculates the flow and power generated based on water levels and the opening of its vanes (similar to a gate).

## Parameters

| Key                  | Type    | Required | Description                                                               |
|----------------------|---------|----------|---------------------------------------------------------------------------|
| `max_flow_area`      | `float` | Yes      | The maximum cross-sectional area for flow at the station in square meters.|
| `discharge_coeff`    | `float` | Yes      | The discharge coefficient for the turbine/flow channel.                   |
| `efficiency`         | `float` | Yes      | The overall efficiency of the generator (0.0 to 1.0).                     |
| `upstream_topic`     | `str`   | Yes      | The topic to subscribe to for the upstream water level.                   |
| `downstream_topic`   | `str`   | Yes      | The topic to subscribe to for the downstream water level.                 |
| `vane_opening_topic` | `str`   | Yes      | The topic to subscribe to for the vane opening command.                   |
| `state_topic`        | `str`   | Yes      | The topic to publish the station's detailed state to.                     |
| `release_topic`      | `str`   | No       | An optional, separate topic to publish only the release flow to.          |

## Publishes To

1.  **State Topic:** The value of the `state_topic` parameter.
    - **Payload:**
      ```json
      {
        "flow": <flow_rate_float>,
        "power_generated": <power_float>
      }
      ```
2.  **Release Topic (Optional):** The value of the `release_topic` parameter.
    - **Payload:**
      ```json
      {
        "value": <flow_rate_float>
      }
      ```

## Subscribes To

1.  **Upstream Level:** The value of the `upstream_topic` parameter.
    - **Expected Payload:** `{"level": <level_float>}`
2.  **Downstream Level:** The value of the `downstream_topic` parameter.
    - **Expected Payload:** `{"level": <level_float>}` or `{"value": <level_float>}`
3.  **Vane Opening:** The value of the `vane_opening_topic` parameter.
    - **Expected Payload:** `{"value": <opening_float>}` where opening is from 0.0 to 1.0.
