# ValveAgent

## Function

A ValveAgent simulates a simple valve. Its primary purpose is to receive an opening command and publish its resulting flow, which can then be used as an input by other agents (like a `TankAgent`).

## Parameters

| Key             | Type          | Required | Description                                                               |
|-----------------|---------------|----------|---------------------------------------------------------------------------|
| `cv`            | `float`       | Yes      | A flow coefficient for the valve.                                         |
| `subscribes_to` | `list[str]` or `str` | Yes      | The topic(s) to subscribe to for the valve opening command. The agent will use the first topic in the list if it is a list. |

## Publishes To

- **Topic:** `state/valve/{agent_id}`
- **Payload:**
  ```json
  {
    "opening": <current_opening_float>,
    "flow": <current_flow_float>
  }
  ```

## Subscribes To

- **Topic:** The first topic specified in the `subscribes_to` parameter.
- **Expected Payload:**
  ```json
  {
    "value": <opening_float>
  }
  ```
  where `opening` is a value between 0.0 (closed) and 1.0 (fully open).
