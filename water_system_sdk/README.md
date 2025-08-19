# CHS-SDK - Code and Functionality Overview

## Product Description: Core vs. Agent Versions

The CHS-SDK architecture has a clear layered design, consisting of a "Core Version" and an "Agent Version" built on top of it.

### Core Version

*   **Core Directory**: `modules/`
*   **Purpose**: Scientific computing kernel and digital twin foundation. The `modules` directory is the technical cornerstone of the entire SDK, providing a professional and complete set of hydrological and hydrodynamic simulation models. This version focuses on accurately simulating the physical world to answer "what if...?" questions.

### Agent Version

*   **Core Directories**: `agents/`, `factory/`, `workflows/`, `interfaces/`, etc., which consume the capabilities of the `modules/`.
*   **Purpose**: Intelligent decision-making and automated control solutions. The Agent Version builds on the digital twin environment provided by the Core Version, offering a toolchain for developing, designing, and deploying "intelligent brains" (Agents). It focuses on answering the question "what should be done next?".

## Corrected Directory Structure and File Functions

*Note: This structure has been updated to reflect the actual state of the codebase. Previous versions of this document were out of sync.*

```
chs_sdk/
├── __init__.py
├── agents/                 # Contains control logic (PID, MPC, etc.)
│   ├── ...
├── components/             # Reusable components like loggers
│   ├── ...
├── core/                   # Heart of the SDK, drives the simulation
│   ├── ...
├── factory/                # Tools for automated design and configuration of agents
│   ├── __init__.py
│   └── mother_machine.py   # High-level engine for running design workflows
├── interfaces/             # Defines standards for module interaction
│   ├── ...
├── modules/                # The scientific computing core (hydro models)
│   ├── ...
├── preprocessing/          # Tools for data cleaning and preparation
│   ├── __init__.py
│   ├── data_processor.py   # Core data cleaning tools (cleaner, resampler)
│   ├── interpolators.py    # Spatial interpolation algorithms (New & Refactored)
│   ├── rainfall_processor.py # Applies interpolation to create rainfall data
│   └── structures.py       # Data structures like RainGauge
├── tools/                  # Adapters for third-party software
│   ├── ...
├── utils/                  # General-purpose helper functions
│   ├── ...
└── workflows/              # Multi-step tasks orchestrating SDK capabilities
    ├── __init__.py
    ├── base_workflow.py
    ├── control_tuning_workflow.py # Logic for optimizing controller params
    └── system_id_workflow.py      # Logic for identifying model params from data
```

*   **agents/**: The brains of the system. Defines the decision-making logic for system control.
*   **components/**: High-level, reusable components with specific functions.
*   **core/**: The heart of the SDK, responsible for driving the entire simulation process.
*   **factory/**: **(Updated Description)** This is the "Design Automation" center. It does not contain a generic trainer or evaluator. Instead, it contains the `MotherMachine`, a powerful tool that automates the design of specific models and controllers by running pre-defined `workflows`. For example, it can take sensor data and automatically generate a calibrated digital twin model.
*   **interfaces/**: The "legal contracts" between modules, defining the standards for their interaction.
*   **modules/**: The scientific computing core for the digital twin, a professional-grade simulation engine.
*   **preprocessing/**: **(Updated Description)** The "data janitors" responsible for processing raw data fed into the SDK. This includes tools for cleaning, resampling, and spatial interpolation. *Note: This module was recently refactored to improve consistency and fix bugs.*
*   **tools/**: Adapters for interacting with industry-standard software.
*   **utils/**: Widely used, low-level utility functions.
*   **workflows/**: The "task directors" that chain together various SDK capabilities into end-to-end task flows, such as identifying a system model from data or tuning a controller. These are called by the `factory/mother_machine.py`.

---

## Service and Developer Experience Features

To improve the usability and expand the service capabilities of the SDK, we have introduced the following core features:

### 1. `SimulationBuilder`: A More Elegant Way to Configure Simulations

Say goodbye to tedious dictionary configurations. We now offer the `SimulationBuilder`, which provides a fluent, object-oriented API for programmatically building simulation tasks through method chaining. This approach leads to cleaner code and provides better autocompletion support in IDEs, reducing configuration errors.

**Example:**
```python
from chs_sdk.simulation_builder import SimulationBuilder

builder = SimulationBuilder()
sdk_config = (builder
    .set_simulation_params(total_time=1000, dt=1.0)
    .add_component(
        name="main_reservoir",
        component_type="ReservoirModel",
        params={"area": 100.0, "initial_level": 5.0}
    )
    .build()
)
```

### 2. Modular Installation: Choose Your Features on Demand

To make the package lighter, we have split the SDK's dependencies into three parts: core, agent, and web service. You can install what you need:

-   **Core (Simulation Engine Only):**
    ```bash
    pip install .
    ```
-   **Agent (Includes ML dependencies):**
    ```bash
    pip install .[agent]
    ```
-   **Web Service (For running the API):**
    ```bash
    pip install .[service]
    ```
-   **Full Version (All features):**
    ```bash
    pip install .[agent,service]
    ```

### 3. FastAPI Web Service: Turn Your Simulation into an API

We have built-in a FastAPI-based web service that allows you to easily expose your simulation capabilities as an API for other systems to call.

**How to Start the Service:**
1.  Ensure you have installed the `service` dependencies: `pip install .[service]`
2.  From the `water_system_sdk` directory, run:
    ```bash
    uvicorn chs_sdk.service.main:app --host 0.0.0.0 --port 8000
    ```
3.  Once the service starts, you can access the interactive API documentation at `http://localhost:8000/docs`.
