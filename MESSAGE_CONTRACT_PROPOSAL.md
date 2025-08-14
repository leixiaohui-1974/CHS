# Message Contract Proposal (for RabbitMQ/MQTT)

This document provides a draft proposal for the JSON message formats to be used for communication between the Python Simulation Core (Algo), the Backend, and potentially other services over a message bus like RabbitMQ or MQTT.

This proposal is intended to be a starting point for discussion with the Jules-Backend team.

## General Message Envelope

To ensure consistency and provide essential metadata for routing and debugging, all messages should be wrapped in a standard envelope.

```json
{
  "timestamp": "2024-07-15T10:00:00.123Z",
  "run_id": "sim_run_xyz_123",
  "message_type": "data_exchange",
  "payload": {
    // The actual message content goes here
  }
}
```

| Key            | Type   | Description                                                                 |
| -------------- | ------ | --------------------------------------------------------------------------- |
| `timestamp`    | String | ISO 8601 timestamp of when the message was generated.                       |
| `run_id`       | String | Unique identifier for the simulation run, provided by the backend on start. |
| `message_type` | String | The type of message contained in the payload, used for decoding/routing.    |
| `payload`      | Object | The message-specific data.                                                  |

---

## Message Types & Payloads

### 1. `simulation_status`

*   **Source**: Backend, Algo Core
*   **Description**: Used to broadcast the status of a simulation run.

**Payload Structure:**

```json
{
  "status": "running", // e.g., "pending", "initializing", "running", "paused", "completed", "failed"
  "details": "Simulation step 500 of 10000 completed.",
  "error_info": null // or an object with error details if status is "failed"
}
```

### 2. `data_exchange`

*   **Source**: Algo Core
*   **Description**: The primary message type for publishing component output data at each time step. This is the "firehose" of simulation data. It should be structured to be efficient.

**Payload Structure:**

This payload bundles all signal updates for a given time step to reduce message overhead.

```json
{
  "time": 50.01, // The current simulation time for this data packet
  "signals": [
    {
      "source_component": "motor_1",
      "source_port": "speed_rpm",
      "value": 1498.5
    },
    {
      "source_component": "inverter_1",
      "source_port": "output_current",
      "value": 4.2
    }
    // ... all other signals that were updated in this time step
  ]
}
```
*Topic Idea*: `simulations.{run_id}.data`

### 3. `log_message`

*   **Source**: Algo Core
*   **Description**: For sending application/debug logs, distinct from simulation data.

**Payload Structure:**

```json
{
  "level": "INFO", // DEBUG, INFO, WARN, ERROR
  "message": "Component 'controller_1' initialized successfully.",
  "component_id": "controller_1"
}
```
*Topic Idea*: `simulations.{run_id}.logs`

### 4. `control_command`

*   **Source**: Backend (or external tool)
*   **Description**: Used to send commands to the simulation engine while it is running.

**Payload Structure:**

```json
{
  "command": "pause", // e.g., "pause", "resume", "stop", "inject_event"
  "parameters": {} // Optional parameters for the command, e.g., for "inject_event"
}
```
*Topic Idea*: `simulations.{run_id}.control`

---

This proposal aims to provide a robust and scalable foundation for our messaging architecture. Looking forward to discussing and refining this with the backend team.
