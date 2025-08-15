# PIDAgent

## Function

A PIDAgent implements a Proportional-Integral-Derivative (PID) controller. It reads a sensor value from a topic, calculates a control action to drive the value towards a setpoint, and publishes that action to another topic.

## Parameters

| Key           | Type         | Required | Description                                                                                                                              |
|---------------|--------------|----------|------------------------------------------------------------------------------------------------------------------------------------------|
| `Kp`          | `float`      | Yes      | The Proportional gain.                                                                                                                   |
| `Ki`          | `float`      | Yes      | The Integral gain.                                                                                                                       |
| `Kd`          | `float`      | Yes      | The Derivative gain.                                                                                                                     |
| `set_point`   | `float`      | No       | The target value for the controller. Defaults to `0.0`. Can be updated dynamically via a macro command.                                  |
| `subscribes_to` | `list[str]`  | Yes      | A list of exactly two topics. The first is for macro commands (setpoint changes), and the second is for the sensor value to be controlled. |
| `publishes_to`  | `str`        | Yes      | The topic to publish the control action to.                                                                                              |
| `output_min`  | `float`      | No       | The minimum value of the control output. Defaults to `None` (no limit).                                                                  |
| `output_max`  | `float`      | No       | The maximum value of the control output. Defaults to `None` (no limit).                                                                  |

## Publishes To

- **Topic:** The value of the `publishes_to` parameter.
- **Payload:**
  ```json
  {
    "value": <control_action_float>
  }
  ```

## Subscribes To

1.  **Macro Command Topic:** The first topic in the `subscribes_to` list.
    - **Expected Payload:** A `MacroCommandMessage` structure, typically for updating the setpoint.
      ```json
      {
        "target_variable": "string",
        "target_value": float,
        "duration_hours": float,
        "strategy": "string"
      }
      ```
2.  **Sensor Topic:** The second topic in the `subscribes_to` list.
    - **Expected Payload:**
      ```json
      {
        "level": <sensor_value_float>
      }
      ```
