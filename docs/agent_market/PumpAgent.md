# PumpAgent

## Function

A PumpAgent simulates a pump station with one or more pumps. It operates as a state machine (`Stopped`, `Starting`, `Running`, `Fault`) and calculates flow based on its pump curve and the inlet/outlet pressures.

## Parameters

| Key                    | Type          | Required | Description                                                                 |
|------------------------|---------------|----------|-----------------------------------------------------------------------------|
| `num_pumps_total`      | `int`         | Yes      | The total number of pumps available in the station.                         |
| `curve_coeffs`         | `list[float]` | Yes      | A list of coefficients for the pump curve polynomial equation.              |
| `inlet_pressure_topic` | `str`         | Yes      | The topic to subscribe to for the inlet pressure.                           |
| `outlet_pressure_topic`| `str`         | Yes      | The topic to subscribe to for the outlet pressure.                          |
| `num_pumps_on_topic`   | `str`         | Yes      | The topic to subscribe to for commands to change the number of active pumps.|
| `state_topic`          | `str`         | Yes      | The topic to publish the pump station's detailed state to.                  |
| `initial_num_pumps_on` | `int`         | No       | The number of pumps that are active at the start. Defaults to `0`.          |

## Publishes To

- **Topic:** The value of the `state_topic` parameter.
- **Payload:**
  ```json
  {
    "flow": <flow_rate_float>,
    "head": <head_float>,
    "power": <power_consumption_float>,
    "num_pumps_on": <active_pumps_int>,
    "status": "<status_string>" // e.g., "stopped", "running", "fault"
  }
  ```

## Subscribes To

1.  **Inlet Pressure:** The value of the `inlet_pressure_topic` parameter.
    - **Expected Payload:** `{"value": <pressure_float>}`
2.  **Outlet Pressure:** The value of the `outlet_pressure_topic` parameter.
    - **Expected Payload:** `{"value": <pressure_float>}`
3.  **Number of Pumps On:** The value of the `num_pumps_on_topic` parameter.
    - **Expected Payload:** `{"value": <num_pumps_int>}`
4.  **Commands:** The agent also subscribes to global command topics:
    - `cmd.pump.start`
    - `cmd.pump.stop`
    - `cmd.pump.fault`
    - `cmd.pump.reset`
