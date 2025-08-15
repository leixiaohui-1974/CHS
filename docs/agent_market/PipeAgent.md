# PipeAgent

## Function

A PipeAgent simulates the flow of water through a pressurized pipe, calculating flow based on the pressure difference between its inlet and outlet.

## Parameters

| Key                     | Type    | Required | Description                                                    |
|-------------------------|---------|----------|----------------------------------------------------------------|
| `length`                | `float` | Yes      | The length of the pipe in meters.                              |
| `diameter`              | `float` | Yes      | The diameter of the pipe in meters.                            |
| `friction_factor`       | `float` | Yes      | The Darcy-Weisbach friction factor for the pipe.               |
| `inlet_pressure_topic`  | `str`   | Yes      | The topic to subscribe to for the inlet pressure.              |
| `outlet_pressure_topic` | `str`   | Yes      | The topic to subscribe to for the outlet pressure.             |
| `state_topic`           | `str`   | Yes      | The topic to publish the pipe's state to.                      |

## Publishes To

- **Topic:** The value of the `state_topic` parameter.
- **Payload:**
  ```json
  {
    "flow": <flow_rate_float>,
    "velocity": <velocity_float>
  }
  ```

## Subscribes To

1.  **Inlet Pressure:** The value of the `inlet_pressure_topic` parameter.
    - **Expected Payload:** `{"pressure": <pressure_float>}`
2.  **Outlet Pressure:** The value of the `outlet_pressure_topic` parameter.
    - **Expected Payload:** `{"pressure": <pressure_float>}`
