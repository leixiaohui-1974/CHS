# DispatchAgent

## Function

The DispatchAgent acts as a high-level strategic coordinator for the system. It can perform long-term optimization to send high-level goals (MacroCommands) to other agents.

## Parameters

| Key              | Type        | Required | Description                                                                                 |
|------------------|-------------|----------|---------------------------------------------------------------------------------------------|
| `control_agents` | `list[str]` | No       | A list of agent IDs that this DispatchAgent will send commands to. Defaults to `[]`.          |
| `publishes_to`   | `list[str]` | No       | A list of topics to publish the macro commands to. The order must match `control_agents`.   |

## Publishes To

- **Topic:** The topics listed in the `publishes_to` parameter. It maps the command to the topic based on the index of the agent in `control_agents`.
- **Payload:** A `MacroCommandMessage` structure.
  ```json
  {
    "target_variable": "string",
    "target_value": float,
    "duration_hours": float,
    "strategy": "string"
  }
  ```

## Subscribes To

- **Topics:** The DispatchAgent currently does not subscribe to specific topics by default configuration. It is designed to be extended to listen for system-wide `awareness` or `alarm` topics.
- **Expected Payload:** Varies depending on the implementation of `on_message`.
  - For `awareness` topics: `dict` containing situational data.
  - For `alarm` topics: `dict` containing details about the alarm.
