# Scenario: Single Tank PID Control

## Business Goal

This scenario demonstrates the most basic feedback control loop in the CHS-SDK. Its purpose is to control the water level of a single water tank using a PID controller. This setup is fundamental for ensuring stability in a water system, such as maintaining a safe level in a reservoir.

## Agent Composition

The scenario consists of the following three agents:

- **`InflowAgent` (inflow_agent_1):** Simulates an external water source. It provides a constant inflow for the first half of the simulation and then stops, creating a disturbance for the PID controller to handle.
- **`TankAgent` (tank_agent_1):** Represents the physical water tank. It has a defined surface area and initial water level. Its level changes based on the inflow from the `InflowAgent` and the outflow controlled by the `PIDAgent`.
- **`PIDAgent` (pid_agent_1):** The controller. It continuously monitors the `TankAgent`'s water level and adjusts the tank's release outflow to try and maintain the level at a predefined setpoint (10.0m).

## Expected Result

The simulation should show the water level of the tank starting at 5.0m and rising towards the setpoint of 10.0m. The PID controller will actively manage the outflow to reach and maintain this level. When the inflow stops at 50 seconds, the controller should reduce the outflow to prevent the tank level from dropping below the setpoint. The final water level should be stable at or very near 10.0m.
