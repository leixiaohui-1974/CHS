# MPCAgent

## Function

An MPCAgent implements a Model Predictive Control (MPC) controller. It uses a predictive model of the system to calculate optimal control actions over a future horizon.

## Parameters

| Key                    | Type          | Required | Description                                                                    |
|------------------------|---------------|----------|--------------------------------------------------------------------------------|
| `prediction_model`     | `BaseModel`   | Yes      | An instance of a system model (e.g., `ReservoirModel`) used for prediction.    |
| `prediction_horizon`   | `int`         | Yes      | The number of future time steps the controller looks ahead.                    |
| `control_horizon`      | `int`         | Yes      | The number of future time steps for which control actions are calculated.      |
| `set_point`            | `float`       | Yes      | The target value for the controlled variable.                                  |
| `q_weight`             | `float`       | Yes      | The weight for the state deviation penalty in the cost function.               |
| `r_weight`             | `float`       | Yes      | The weight for the control action penalty in the cost function.                |
| `u_min`                | `float`       | Yes      | The minimum value of the control output.                                       |
| `u_max`                | `float`       | Yes      | The maximum value of the control output.                                       |
| `state_topic`          | `str`         | Yes      | The topic to subscribe to for the current state of the system.                 |
| `disturbance_topic`    | `str`         | No       | The topic to subscribe to for disturbance forecasts (e.g., predicted rainfall).|
| `output_topic`         | `str`         | Yes      | The topic to publish the control action to.                                    |

## Publishes To

- **Topic:** The value of the `output_topic` parameter.
- **Payload:**
  ```json
  {
    "value": <control_action_float>
  }
  ```

## Subscribes To

1.  **State Topic:** The value of the `state_topic` parameter.
    - **Expected Payload:**
      ```json
      {
        "level": <state_value_float>
      }
      ```
      *(Note: Also accepts "output" as a key)*

2.  **Disturbance Topic (Optional):** The value of the `disturbance_topic` parameter.
    - **Expected Payload:**
      ```json
      {
        "forecast": [<value1>, <value2>, ...]
      }
      ```
