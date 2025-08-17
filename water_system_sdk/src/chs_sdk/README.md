# CHS-SDK: A Comprehensive Toolkit for Water System Simulation and Control

Welcome to the `chs-sdk`, a powerful and flexible Python-based software development kit for the simulation, analysis, and intelligent control of water systems.

## Overview

The `chs-sdk` is designed with a two-layer architecture:

1.  **Core Scientific Engine (`modules/`)**: At its heart, the SDK provides a robust set of tools for creating high-fidelity digital twins of water systems. This layer is focused on accurately modeling the physics of water flow, from rainfall-runoff processes in watersheds to complex hydrodynamics in rivers and channels. It answers the question: *"What will happen if...?"*

2.  **Intelligent Agent Framework (`agents/`, `factory/`, etc.)**: Built on top of the core engine, this layer provides a complete framework for developing, training, and deploying intelligent agents that can make decisions and control the simulated water system. It answers the question: *"What should we do next?"*

This dual-layer design allows for a clear separation of concerns, making the SDK suitable for a wide range of applications, from purely scientific research to the development of real-time, autonomous control systems.

## Directory Structure and Key Components

Here is a breakdown of the main directories within the `chs-sdk` and their functions:

*   `main.py`
    *   **Purpose**: Main entry point for running simulations.
    *   **Key Components**: Parses configuration files, sets up the simulation environment, and starts the simulation loop.

*   `simulation_manager.py`
    *   **Purpose**: Orchestrates the entire simulation process.
    *   **Key Components**: Manages the simulation time, coordinates the execution of agents and models, and handles data logging.

*   `config_parser.py`
    *   **Purpose**: Handles the loading and validation of simulation configuration files.
    *   **Key Components**: Ensures that the simulation is set up with valid parameters and a correct topology.

### `agents/` - The Brains of the System

This directory contains the logic for decision-making and control.

*   **`base.py`**: Defines the `BaseAgent`, the fundamental building block for all intelligent agents. It provides a common interface for agent lifecycle management (`setup`, `execute`, `shutdown`), message handling, and state management.
*   **`control_agent.py`**: Implements the `ControlAgent`, which is responsible for controlling actuators in the simulation (e.g., gates, pumps, valves). It can host various control algorithms, such as PID or MPC.
*   **`perception_agent.py`**: Responsible for gathering and processing data from sensors in the simulation to form a coherent understanding of the system's state.
*   **`dispatch_agent.py`**: A higher-level agent that coordinates the actions of multiple other agents based on a system-wide strategy.
*   **`message.py` & `message_bus.py`**: These files define the communication system that allows agents to exchange information and commands.

### `modules/` - The Scientific Computing Core

This is the digital twin engine, containing all the physics-based models.

*   **`hydrology/`**: Models for simulating the water cycle at the watershed level.
    *   **`core.py`**: Contains the main orchestration logic for hydrological simulations, including the `Basin`, `SubBasin`, and `Reservoir` classes.
    *   **Runoff Models**: Implements different models for calculating runoff from rainfall (e.g., `XinanjiangModel`).
    *   **Routing Models**: Implements models for routing water flow through river reaches (e.g., `MuskingumModel`).
*   **`hydrodynamics/`**: Models for simulating detailed water flow in open channels and pipe networks based on principles of fluid dynamics.
    *   **`solver.py`**: Contains numerical solvers for the Saint-Venant equations, which govern open-channel flow.
    *   **`network.py`**: Tools for building and managing networks of nodes and reaches.
*   **`modeling/`**: A comprehensive library of component models that can be assembled to create a full system model.
    *   **`storage_models.py`**: Models for reservoirs, tanks, etc.
    *   **`channel_models.py`**: Models for river and canal segments.
    *   **`control_structure_models.py`**: Models for gates, weirs, etc.
    *   **`pump_models.py`, `valve_models.py`**: Models for various types of actuators.
*   **`control/`**: Contains the implementations of various control algorithms.
    *   **`pid_controller.py`**: A standard Proportional-Integral-Derivative (PID) controller.
    *   **`mpc_controller.py`**: A Model Predictive Control (MPC) controller for more advanced, optimized control.
    *   **`kalman_filter.py`**: Tools for state estimation and data assimilation.

### Other Key Directories

*   **`core/`**: The heart of the SDK, responsible for driving the simulation loop and managing the overall system state.
*   **`factory/`**: A "factory" for building, training, and evaluating intelligent agents, particularly for reinforcement learning applications.
*   **`workflows/`**: High-level scripts that chain together various SDK functionalities to perform complex, end-to-end tasks like system identification or controller tuning.
*   **`preprocessing/`**: Tools for cleaning, preparing, and transforming raw input data (e.g., rainfall time series, GIS data) into a format suitable for the SDK.
*   **`utils/`**: A collection of helper functions and utilities used throughout the SDK.

## Getting Started

To begin using the `chs-sdk`, start by exploring the examples in the `examples/` directory. These provide practical demonstrations of how to set up and run simulations for various scenarios, from a single reservoir to a complex river network.
