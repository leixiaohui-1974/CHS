# Chapter 3: Your First Simulation - A Single Reservoir

In this chapter, you will learn the fundamental concepts of the `chs-sdk`'s simulation engine by building and running a model of a single water reservoir.

## The Core Concepts

At the heart of the `chs-sdk`'s "Core Version" are three main concepts:

1.  **Entities**: These are the physical components of your water system, such as reservoirs, channels, pumps, and gates. In the SDK, these are often represented as "agents". Each entity has a mathematical model that describes its behavior.
2.  **Connections**: These define how your entities are connected to each other, creating a network that represents your complete water system.
3.  **Host**: This is the engine that drives the simulation. It manages the simulation time, executes the models for each entity at each time step, and collects the results.

## Scenario: A Simple Reservoir

Our goal is to simulate a reservoir with the following characteristics:

*   It has an initial amount of water.
*   It receives a constant inflow of water.
*   It has an outlet, and the outflow is proportional to the amount of water currently in the reservoir (this is a simple "linear reservoir" model).

We want to observe how the water level in the reservoir changes over a 24-hour period.

## Building the Simulation Script

Let's write a Python script to build and run this simulation. Create a new file named `run_reservoir_sim.py`.

### Step 1: Import Necessary Classes

First, we need to import the classes we'll be using from the SDK.

```python
import matplotlib.pyplot as plt

# The Host is the main simulation environment
from chs_sdk.core.host import Host
# This is the agent that will represent our reservoir
from chs_sdk.modules.modeling.storage_models import FirstOrderStorageModel
# This agent will provide a constant inflow
from chs_sdk.modules.disturbances.predefined import ConstantDisturbance
```

### Step 2: Create a Host for the Simulation

The `Host` is the main container for our simulation environment.

```python
# Create a simulation host
host = Host()
```

### Step 3: Define the Reservoir Model

Now, let's create our reservoir. We'll use the `FirstOrderStorageModel`. This is a simple but common model where the outflow is directly proportional to the storage. We need to give it a name, an initial amount of stored water, and a `time_constant` which determines how quickly it drains.

```python
# Create the reservoir model agent
reservoir_agent = FirstOrderStorageModel(
    name='MyReservoir',
    initial_value=10.0,  # Starting with 10 units of water
    time_constant=5.0  # A larger constant means slower outflow
)
```

### Step 4: Define a Disturbance (Inflow)

Our reservoir needs an inflow of water. We'll create a constant inflow of 5 units per time step using the `ConstantDisturbance` class.

```python
# Create a constant inflow disturbance agent
inflow_agent = ConstantDisturbance(
    name='inflow',
    constant_value=5.0
)
```

### Step 5: Register the Components and Connections

Now we need to tell the `Host` about our reservoir and the inflow. We also need to define how they are connected.

```python
# Add the agents to the host
host.add_agent(reservoir_agent)
host.add_agent(inflow_agent)

# Connect the inflow's output to the reservoir's inflow input
host.add_connection(
    source_agent_name='inflow',
    target_agent_name='MyReservoir',
    source_port_name='value',
    target_port_name='inflow'
)
```
This tells the simulation that the `value` from the `inflow` agent should feed into the `inflow` port of the `MyReservoir` agent at each time step.

### Step 6: Run the Simulation

With everything set up, we can now run the simulation. We'll run it for 24 time steps, with each step representing 1 hour.

```python
# Run the simulation for 24 steps, with a step size of 1 hour
host.run(num_steps=24, dt=1.0)
```

### Step 7: Visualize the Results

The `Host` automatically logs the state of all components during the simulation. We can get this data as a pandas DataFrame and plot it to see the results.

```python
# Get the results from the data logger
results_df = host.get_datalogger().get_as_dataframe()

# Plot the storage of the reservoir over time
plt.figure(figsize=(10, 6))
plt.plot(results_df.index, results_df['MyReservoir.value'], label='Reservoir Storage')
plt.xlabel('Time (hours)')
plt.ylabel('Storage (units)')
plt.title('Reservoir Simulation Results')
plt.grid(True)
plt.legend()
plt.show()
```

## The Complete Script

Here is the complete `run_reservoir_sim.py` script:

```python
import matplotlib.pyplot as plt

from chs_sdk.core.host import Host
from chs_sdk.modules.modeling.storage_models import FirstOrderStorageModel
from chs_sdk.modules.disturbances.predefined import ConstantDisturbance

# 1. Create a simulation host
host = Host()

# 2. Define the reservoir model agent
reservoir_agent = FirstOrderStorageModel(
    name='MyReservoir',
    initial_value=10.0,
    time_constant=5.0
)

# 3. Define a constant inflow disturbance agent
inflow_agent = ConstantDisturbance(
    name='inflow',
    constant_value=5.0
)

# 4. Register the components and connections
host.add_agent(reservoir_agent)
host.add_agent(inflow_agent)
host.add_connection(
    source_agent_name='inflow',
    target_agent_name='MyReservoir',
    source_port_name='value',
    target_port_name='inflow'
)

# 5. Run the simulation
host.run(num_steps=24, dt=1.0)

# 6. Visualize the results
results_df = host.get_datalogger().get_as_dataframe()
print("Simulation Results:")
print(results_df)

plt.figure(figsize=(10, 6))
plt.plot(results_df.index, results_df['MyReservoir.value'], label='Reservoir Storage')
plt.xlabel('Time (hours)')
plt.ylabel('Storage (units)')
plt.title('Reservoir Simulation Results')
plt.grid(True)
plt.legend()
plt.show()

```

When you run this script, you should see a plot showing the water storage in the reservoir starting at 10 units and gradually increasing towards a steady state.

Congratulations! You have successfully built and run your first simulation with the `chs-sdk`. In the next chapter, we will learn how to add a controller to automatically manage the reservoir's water level.
