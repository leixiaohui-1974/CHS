# DataLoggerAgent

## Function

A DataLoggerAgent is a utility agent used for debugging and monitoring. It subscribes to one or more topics (including wildcards) and prints any message it receives to the console.

## Parameters

| Key               | Type        | Required | Description                                                                                              |
|-------------------|-------------|----------|----------------------------------------------------------------------------------------------------------|
| `topics_to_log`   | `list[str]` | No       | A list of topics to subscribe to. Can use MQTT-style wildcards (`#` for all, `+` for single level). Defaults to `["#"]`. |

## Publishes To

This agent does not publish any messages.

## Subscribes To

- **Topics:** The topics specified in the `topics_to_log` list.
- **Expected Payload:** Any valid message payload. The agent will print the entire message structure.
