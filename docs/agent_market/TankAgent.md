# TankAgent

## Function

A TankAgent simulates a water reservoir. It maintains a water level based on inflows and outflows. It can optionally use a Kalman Filter to assimilate real-world sensor data and correct its internal state.

## Parameters

| Key           | Type    | Required | Description                                                               |
|---------------|---------|----------|---------------------------------------------------------------------------|
| `area`        | `float` | Yes      | The surface area of the tank in square meters.                            |
| `initial_level` | `float` | Yes      | The initial water level in the tank at the start of the simulation.       |
| `max_level`   | `float` | No       | The maximum water level of the tank. Defaults to `20.0`.                  |
| `publishes_to`| `str`   | No       | The topic to publish the tank's state to. Defaults to `tank/{agent_id}/state`. |
| `subscribes_to`| `list[str]`| No    | A list of topics to subscribe to for inflows and outflows.                |
| `enable_kalman_filter` | `bool` | No | Enables the Kalman Filter for data assimilation. Defaults to `False`.   |
| `kalman_filter` | `dict` | No      | A dictionary of Kalman Filter parameters (F, H, Q, R, x0, P0).            |

## Publishes To

- **Topic:** The value of the `publishes_to` parameter, or the default `tank/{agent_id}/state`.
- **Payload:**
  ```json
  {
    "level": <current_water_level_float>,
    "inflow": <current_inflow_float>,
    "outflow": <current_outflow_float>
  }
  ```

## Subscribes To

The `TankAgent` subscribes to topics based on string matching. The `on_message` method routes messages to different inputs of the model based on the topic name.

1.  **Inflow:** Any topic in `subscribes_to` that starts with `data.inflow`.
    - **Expected Payload:** `{"value": <inflow_float>}`
2.  **Release Outflow:** Any topic in `subscribes_to` that starts with `state/valve/`.
    - **Expected Payload:** `{"flow": <outflow_float>}`
3.  **Demand Outflow:** Any topic in `subscribes_to` that starts with `demand/`.
    - **Expected Payload:** `{"value": <demand_float>}`
4.  **Measurement (for Kalman Filter):** If the Kalman Filter is enabled, it automatically subscribes to `measurement/level/{agent_id}`.
    - **Expected Payload:** `{"value": <measured_level_float>}`
