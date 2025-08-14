# Configuration Contract for CHS Simulation

This document defines the definitive structure of the `config` dictionary used to configure and launch a simulation. This contract is the "single source of truth" for the Python SDK, the backend services, and the frontend graphical modeling interface.

## Root Structure

The `config` object is a JSON dictionary with the following top-level keys:

```json
{
  "simulation_params": {},
  "components": [],
  "connections": [],
  "execution_order": [],
  "logger_config": {},
  "events": []
}
```

---

## 1. `simulation_params`

Defines the core parameters of the simulation run.

*   **Type**: `Object`
*   **Description**: Contains settings that control the overall simulation behavior, such as timing and execution mode.

| Key             | Type    | Description                                                                                             | Example                          |
| --------------- | ------- | ------------------------------------------------------------------------------------------------------- | -------------------------------- |
| `duration`      | Number  | Total duration of the simulation in seconds.                                                            | `1000`                           |
| `time_step`     | Number  | The discrete time step for the simulation loop in seconds.                                              | `0.01`                           |
| `mode`          | String  | Execution mode. Can be `real-time`, `as-fast-as-possible`, or `step-by-step`.                             | `"as-fast-as-possible"`          |
| `start_time`    | String  | Optional. The start time of the simulation in ISO 8601 format. Defaults to the current system time.     | `"2024-01-01T00:00:00Z"`         |

---

## 2. `components`

An array of objects, where each object defines a component instance in the simulation.

*   **Type**: `Array<Object>`
*   **Description**: This is the library of all instantiated components, including physical models, control agents, sensors, etc.

### Component Object Structure

| Key           | Type   | Description                                                                                             | Example                                     |
| ------------- | ------ | ------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| `id`          | String | A unique identifier for the component instance within the simulation.                                   | `"motor_1"`                                 |
| `type`        | String | The registered type of the component, which maps to a specific Python class.                            | `"DCMotor"`                                 |
| `params`      | Object | A dictionary of parameters required to initialize this specific component instance.                     | `{"voltage": 24, "resistance": 0.5}`        |
| `metadata`    | Object | Optional. Contains non-functional data, such as UI positioning for the frontend.                        | `{"ui": {"x": 100, "y": 250}}`              |

---

## 3. `connections`

An array of objects, defining the data flow and relationships between components.

*   **Type**: `Array<Object>`
*   **Description**: This represents the "wiring" or "neural connections" of the system, linking outputs of one component to inputs of another.

### Connection Object Structure

| Key           | Type   | Description                                                                                                   | Example                                                 |
| ------------- | ------ | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| `id`          | String | A unique identifier for the connection.                                                                       | `"conn_sensor_to_controller"`                           |
| `type`        | String | The type of connection. Examples: `data`, `control`, `feedback`. This can influence routing or middleware QoS. | `"data"`                                                |
| `source`      | Object | Defines the origin of the connection.                                                                         | `{"component_id": "motor_1", "port": "speed_rpm"}`      |
| `target`      | Object | Defines the destination of the connection.                                                                    | `{"component_id": "controller_1", "port": "speed_in"}` |
| `metadata`    | Object | Optional. Contains non-functional data, such as UI rendering hints for the connection line.                   | `{"ui": {"path": "smooth"}}`                             |

---

## 4. `execution_order`

An array of arrays, defining the execution sequence of components at each simulation step.

*   **Type**: `Array<Array<String>>`
*   **Description**: Components within the same inner array can be executed in parallel. The outer array defines the sequential order of these parallel groups.

### Example

```json
"execution_order": [
  ["sensor_1", "sensor_2"],      // Step 1: Read from sensors in parallel
  ["controller_1"],              // Step 2: Run the controller
  ["plant_model_1", "plant_model_2"] // Step 3: Update the plant models in parallel
]
```

---

## 5. `logger_config`

Defines how simulation data should be logged.

*   **Type**: `Object`
*   **Description**: Specifies which data points to record and the format/destination for the logs.

### Logger Config Structure

| Key           | Type            | Description                                                                                              | Example                                |
| ------------- | --------------- | -------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| `level`       | String          | The global logging level (`DEBUG`, `INFO`, `WARN`, `ERROR`).                                             | `"INFO"`                               |
| `targets`     | Array<Object>   | An array defining logging destinations (e.g., file, database, console).                                  | `[{"type": "csv", "filename": "sim_output.csv"}]` |
| `signals_to_log` | Array<Object>   | Specifies which component signals to log.                                                                | `[{"component_id": "motor_1", "port": "speed_rpm"}]` |

---

## 6. `events`

An array of objects that define discrete events to be injected into the simulation.

*   **Type**: `Array<Object>`
*   **Description**: Used for fault injection, scenario changes, or any other scheduled, discrete action.

### Event Object Structure

| Key        | Type   | Description                                                                                                 | Example                                                               |
| ---------- | ------ | ----------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `id`       | String | A unique identifier for the event.                                                                          | `"event_motor_fault"`                                                 |
| `trigger`  | Object | The condition that triggers the event. Can be time-based or state-based.                                    | `{"type": "time", "value": 500}` (i.e., at 500 seconds)                |
| `action`   | Object | The action to be performed when the event is triggered. This usually involves modifying a component's state. | `{"target": "motor_1.params.resistance", "operation": "set", "value": 100}` |
