# Chapter 4: Introducing Intelligent Control with PID

In the last chapter, we simulated a reservoir with a constant inflow. This is called an "open-loop" system because there is no feedback to control the outcome.

In this chapter, we will close the loop. We will introduce a **PID Controller Agent** to automatically adjust the inflow to the reservoir to maintain a desired water level, or **setpoint**. This is your first step into the "Agent Version" of the `chs-sdk`.

## What is a PID Controller?

A PID (Proportional-Integral-Derivative) controller is one of the most common control algorithms used in industry. It continuously calculates an "error" value as the difference between a desired setpoint and a measured process variable and applies a correction based on proportional, integral, and derivative terms.

*   **Proportional (P)**: Reacts to the current error. A larger error results in a larger correction.
*   **Integral (I)**: Considers the accumulation of past errors. This helps eliminate steady-state errors.
*   **Derivative (D)**: Responds to the rate at which the error is changing. This helps to dampen oscillations.

Don't worry if this seems complicated. The `chs-sdk` provides a ready-to-use `PIDController` agent that handles all the math for us.

## Scenario: Maintaining a Reservoir Level

Our goal is to modify the simulation from the previous chapter. Instead of a constant inflow, we will have a controllable inflow. A PID controller will observe the water level in the reservoir and adjust the inflow to keep the level at a setpoint of 15 units.

## Modifying the Simulation Script

Let's modify our `run_reservoir_sim.py` script.

### Step 1: Import the PIDController

First, we need to import the `PIDController` class.

```python
# In addition to previous imports
from chs_sdk.modules.control.pid_controller import PIDController
```

### Step 2: Create the PID Controller Agent

Now, let's create an instance of the `PIDController`. We need to provide it with the P, I, and D tuning parameters (`kp`, `ki`, `kd`) and our desired `setpoint`.

```python
# Create the PID controller agent
pid_agent = PIDController(
    name='MyPIDController',
    kp=1.5,
    ki=0.1,
    kd=0.5,
    setpoint=15.0  # Our target water level
)
```
Finding the right values for `kp`, `ki`, and `kd` is called "tuning," and it's a key part of control engineering. For now, we'll use these example values.

### Step 3: Update the Connections

This is the most important part. We need to wire our new controller into the system.

1.  The PID controller needs to **know the current water level** of the reservoir. So, we connect the reservoir's output to the controller's input.
2.  The PID controller will **calculate the required inflow**. So, we connect the controller's output to the reservoir's inflow input.

Our old `inflow_agent` is no longer needed, as the PID controller is now in charge of the inflow.

```python
# The Host and Reservoir are created as before...

# Add the agents to the host
host.add_agent(reservoir_agent)
host.add_agent(pid_agent)

# --- New Connections ---
# 1. Connect reservoir's level to the PID's measurement input
host.add_connection(
    source_agent_name='MyReservoir',
    target_agent_name='MyPIDController',
    source_port_name='value',
    target_port_name='measured_value'
)

# 2. Connect the PID's output to the reservoir's inflow
host.add_connection(
    source_agent_name='MyPIDController',
    target_agent_name='MyReservoir',
    source_port_name='output',
    target_port_name='inflow'
)
```

### Step 4: Update the Plotting

Let's update our plotting code to also show the setpoint and the controller's output (the inflow it's commanding).

```python
# Get the results
results_df = host.get_datalogger().get_as_dataframe()

# Plot the results
plt.figure(figsize=(12, 8))

# Plot 1: Reservoir Storage
plt.subplot(2, 1, 1)
plt.plot(results_df.index, results_df['MyReservoir.value'], label='Reservoir Storage')
# Add a line for the setpoint
plt.axhline(y=15.0, color='r', linestyle='--', label='Setpoint (15.0)')
plt.title('Reservoir Storage Level')
plt.ylabel('Storage (units)')
plt.legend()
plt.grid(True)

# Plot 2: Controller Output
plt.subplot(2, 1, 2)
plt.plot(results_df.index, results_df['MyPIDController.output'], label='PID Output (Inflow)')
plt.title('Controller Output')
plt.ylabel('Flow (units)')
plt.xlabel('Time (hours)')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()
```

## The Complete Script

Here is the new, complete script:

```python
import matplotlib.pyplot as plt

from chs_sdk.core.host import Host
from chs_sdk.modules.modeling.storage_models import FirstOrderStorageModel
from chs_sdk.modules.control.pid_controller import PIDController

# 1. Create a simulation host
host = Host()

# 2. Define the reservoir model agent
reservoir_agent = FirstOrderStorageModel(
    name='MyReservoir',
    initial_value=10.0,
    time_constant=5.0
)

# 3. Create the PID controller agent
pid_agent = PIDController(
    name='MyPIDController',
    kp=1.5,
    ki=0.1,
    kd=0.5,
    setpoint=15.0
)

# 4. Register agents and connections
host.add_agent(reservoir_agent)
host.add_agent(pid_agent)

# Connect reservoir level to PID input
host.add_connection(
    source_agent_name='MyReservoir',
    target_agent_name='MyPIDController',
    source_port_name='value',
    target_port_name='measured_value'
)

# Connect PID output to reservoir inflow
host.add_connection(
    source_agent_name='MyPIDController',
    target_agent_name='MyReservoir',
    source_port_name='output',
    target_port_name='inflow'
)

# 5. Run the simulation
host.run(num_steps=50, dt=1.0) # Run for longer to see it stabilize

# 6. Visualize the results
results_df = host.get_datalogger().get_as_dataframe()
print("Simulation Results:")
print(results_df.head())

plt.figure(figsize=(12, 8))

plt.subplot(2, 1, 1)
plt.plot(results_df.index, results_df['MyReservoir.value'], label='Reservoir Storage')
plt.axhline(y=15.0, color='r', linestyle='--', label='Setpoint (15.0)')
plt.title('Reservoir Storage Level')
plt.ylabel('Storage (units)')
plt.legend()
plt.grid(True)

plt.subplot(2, 1, 2)
plt.plot(results_df.index, results_df['MyPIDController.output'], label='PID Output (Inflow)')
plt.title('Controller Output')
plt.ylabel('Flow (units)')
plt.xlabel('Time (hours)')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()
```

When you run this script, you will see the PID controller in action. The water level will start at 10, and the controller will command a high inflow to raise it. As the level approaches the setpoint of 15, the controller will reduce the inflow, eventually settling on an inflow rate that keeps the water level stable at the setpoint.

You have now successfully used an intelligent agent to control a simulation! In the next chapters, we will explore more advanced control methods and how to build more complex system models.
