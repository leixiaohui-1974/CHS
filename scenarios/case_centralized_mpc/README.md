# Scenario: Centralized MPC Control of Two Tanks

## Business Goal

This scenario demonstrates a hierarchical control strategy. A high-level `DispatchAgent` uses a centralized Model Predictive Control (MPC) approach to coordinate two separate water tanks. The goal is to show how a central "brain" can manage multiple subsystems to achieve a global objective, such as maintaining balanced water levels across a network.

## Agent Composition

This scenario features a more complex, multi-layered agent society:

- **`DispatchAgent` (central_dispatch_brain):** The strategic layer. It monitors the state of the entire system (both tanks and the main inflow) and sends high-level commands (e.g., "target level for tank 1 should be 8.0m over the next 2 hours") to the tactical agents.
- **`PIDAgent` (pid_controller_1, pid_controller_2):** The tactical layer. Each PID controller is responsible for a single tank. It receives macro commands from the `DispatchAgent` and translates them into concrete, low-level actions (i.e., adjusting a valve opening) to meet the target set by the dispatch brain.
- **`InflowAgent` (main_inflow_source):** Simulates the main river or water source that feeds both tanks.
- **`TankAgent` (storage_tank_1, storage_tank_2):** The physical layer. These agents represent the two water tanks being controlled.
- **`ValveAgent` (outlet_valve_1, outlet_valve_2):** The actuator layer. These valves are the physical devices that the PID agents control to manage the outflow from each tank.

## Expected Result

The `DispatchAgent` should be observed sending macro commands to the two `PIDAgent`s. In response, each `PIDAgent` will control its respective `ValveAgent` to manipulate the water level in its `TankAgent`. The water levels in both tanks should change in a coordinated fashion, following the high-level strategy dictated by the central dispatch brain, rather than just reacting independently. This demonstrates a more sophisticated, managed control hierarchy.
