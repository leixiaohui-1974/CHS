# Scenario: Kernel Fault Tolerance

## Business Goal

This scenario is a technical test case designed to verify the robustness of the core simulation kernel. The goal is to ensure that if one agent in the society experiences a critical error and fails, it does not crash the entire simulation. The rest of the agents should continue to operate normally. This is crucial for building resilient and reliable systems.

## Agent Composition

This scenario uses special agents defined within its own directory:

- **`DummyAgent` (dummy_agent_1, dummy_agent_2):** These are simple, well-behaved agents. Their only job is to print a message at each time step to show that they are running.
- **`FaultyAgent` (faulty_agent_1):** This is a purpose-built "bad" agent. It is configured to run normally for a few steps and then deliberately raise an exception, simulating a crash.

## Expected Result

The simulation will start, and all three agents will print their "running" messages for the first few seconds. At `t=4.0s`, the `FaultyAgent` will raise an exception and print an error message. The key result is that the simulation **does not stop**. The two `DummyAgent`s should continue to execute and print their messages for the remainder of the simulation duration, proving that the kernel has successfully isolated the failure of the single agent.
