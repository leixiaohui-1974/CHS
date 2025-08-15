# Scenario: River System Simulation

## Business Goal

This scenario demonstrates the integration of multiple "body" agents to simulate a more complex, realistic water system. It models a river that flows into a reservoir, which then releases water through a hydropower station into a downstream river. The goal is to verify that different types of agents can be connected together correctly to form a larger, functional digital twin.

## Agent Composition

This scenario is composed of a chain of agents, each feeding into the next:

- **`InflowAgent` (inflow_source):** The starting point. It generates a constant inflow of water.
- **`ChannelAgent` (river1):** Simulates the first stretch of the river, taking the inflow from the source and routing it towards the reservoir. This introduces a realistic time delay and attenuation to the flow.
- **`TankAgent` (main_reservoir):** Represents the reservoir that stores the water from the upstream river.
- **`HydropowerStationAgent` (hydro_station):** Simulates the power plant. It draws water from the reservoir and releases it downstream. Its operation depends on the reservoir's water level and a vane opening command.
- **`ChannelAgent` (river2):** Simulates the second stretch of the river, downstream of the power station.
- **`InflowAgent` (tailwater_source, vane_control):** These are used as "dummy" agents to provide constant values for the downstream water level and the hydropower vane opening, simplifying the simulation.
- **`DataLoggerAgent` (data_logger):** A utility agent that subscribes to all topics (`#`) and prints the messages, allowing the user to observe the interactions between all agents in the system.

## Expected Result

The simulation should show a logical progression of water through the system. The `inflow_source` will publish a constant flow, which will be received by `river1`. After a delay, the outflow from `river1` will become the inflow for the `main_reservoir`, causing its water level to rise. The `hydro_station` will draw water from the reservoir, and its outflow will be visible in the logs. Finally, `river2` will receive the flow from the station. The `DataLoggerAgent` will print a continuous stream of messages, showing the state changes and interactions of all agents at each time step.
