# ChannelAgent

## Function

A ChannelAgent simulates the flow of water through an open channel using the Muskingum routing model. This model simulates the delay and attenuation of a flood wave as it travels down a river or channel.

## Parameters

| Key             | Type    | Required | Description                                                                                             |
|-----------------|---------|----------|---------------------------------------------------------------------------------------------------------|
| `K`             | `float` | Yes      | The Muskingum storage time constant (in seconds). Represents the travel time of the flood wave.         |
| `x`             | `float` | Yes      | The Muskingum weighting factor (dimensionless, between 0 and 0.5). Controls the amount of attenuation.    |
| `initial_outflow` | `float` | Yes      | The initial outflow from the channel at the start of the simulation.                                    |
| `inflow_topic`  | `str`   | Yes      | The topic to subscribe to for the inflow to the channel.                                                |
| `state_topic`   | `str`   | Yes      | The topic to publish the channel's outflow state to.                                                    |

## Publishes To

- **Topic:** The value of the `state_topic` parameter.
- **Payload:**
  ```json
  {
    "outflow": <outflow_rate_float>
  }
  ```

## Subscribes To

- **Topic:** The value of the `inflow_topic` parameter.
- **Expected Payload:** The agent is flexible and can handle different payload structures. It tries to find the flow value using the keys `"value"`, `"flow"`, or `"outflow"` in the payload dictionary.
  - Example: `{"value": <inflow_float>}`
  - Example: `{"flow": <inflow_float>}`
