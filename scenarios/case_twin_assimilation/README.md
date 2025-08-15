# Scenario: Digital Twin Data Assimilation

## Business Goal

This scenario demonstrates the "digital twin" concept, where a simulation model is continuously corrected by real-world data. The goal is to show how a `TankAgent`'s internal model can be fused with an external data source (simulated by a CSV file) using a Kalman Filter. This creates a high-fidelity digital twin that is more accurate than the model or the sensor data alone.

## Agent Composition

- **`FileAdapterAgent` (sensor_file_adapter):** This agent simulates a real-world sensor. It reads from the `noisy_sensor_data.csv` file at each time step and publishes the "measured" water level to a topic.
- **`TankAgent` (tank1):** This is the core of the digital twin. It runs its own internal physics-based model, but it is also configured with `enable_kalman_filter: True`. This tells the agent to subscribe to the measurement topic and use the incoming data to correct its own state, blending the prediction with the measurement.
- **`DataLoggerAgent` (logger):** A utility agent that logs both the raw "sensor" data from the `FileAdapterAgent` and the corrected, internal state of the `TankAgent`.

## Expected Result

When observing the output log, two sets of data will be visible:
1.  The raw, noisy measurement from `measurement/level/tank1`.
2.  The filtered, internal state from `tank/tank1/state`.

The key result is that the `TankAgent`'s state will be a smoothed, more stable version of the noisy sensor data. The Kalman Filter will effectively reduce the noise and produce a more reliable estimate of the true water level, demonstrating the core value of a data-assimilating digital twin.
