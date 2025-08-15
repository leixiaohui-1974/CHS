# CHS-SDK Service

This service exposes the core functionalities of the CHS-SDK via a RESTful API using FastAPI. It allows other services to run simulations and execute cognitive workflows without needing to directly integrate with the Python SDK.

## Setup and Installation

### 1. Install Dependencies

The service and the underlying SDK have several Python dependencies. Ensure you have Python 3.8+ installed. The required packages can be installed from the root of the repository using `pip`:

```bash
pip install -r requirements.txt
```

Additionally, the FastAPI service requires `uvicorn` and `fastapi`, which can be installed via:

```bash
pip install fastapi "uvicorn[standard]"
```

### 2. Running the Service

To run the service, execute the following command from the **root directory** of the project. It's crucial to run from the root so that the `chs_sdk` module can be found.

```bash
PYTHONPATH=water_system_sdk/src uvicorn chs_sdk_service.main:app --host 0.0.0.0 --port 8000
```

- `PYTHONPATH=water_system_sdk/src`: This is essential for the service to locate the SDK modules.
- `--host 0.0.0.0`: Makes the service accessible from outside the container/machine.
- `--port 8000`: The port the service will run on.

Once running, the API documentation will be available at `http://127.0.0.1:8000/docs`.

## API Endpoints

### System

#### `GET /health`

- **Description**: A simple health check endpoint to verify that the service is running.
- **Request Body**: None.
- **Response**:
  ```json
  {
    "status": "ok"
  }
  ```

### API V1

#### `POST /api/v1/run_simulation`

- **Description**: Runs a complete simulation scenario based on a provided configuration. The service injects a data capture agent to record all simulation messages and returns them.
- **Request Body**: A `ScenarioConfig` JSON object.
  ```json
  {
    "simulation_settings": {
      "duration": 10,
      "time_step": 1.0
    },
    "agent_society": [
      {
        "id": "inflow_agent_1",
        "class": "chs_sdk.agents.disturbance_agents.InflowAgent",
        "params": {
          "topic": "tank/main_tank/inflow",
          "rainfall_pattern": [10, 10, 5, 5]
        }
      },
      {
        "id": "main_tank",
        "class": "chs_sdk.agents.body_agents.TankAgent",
        "params": {
          "area": 100.0
        }
      }
    ]
  }
  ```
- **Success Response**: A JSON object containing the captured simulation data.
  ```json
  {
    "data": [
      {
        "time": 0.0,
        "topic": "tank/main_tank/inflow",
        "sender_id": "inflow_agent_1",
        "payload": { "value": 10 }
      },
      ...
    ]
  }
  ```

#### `POST /api/v1/run_workflow/{workflow_name}`

- **Description**: Executes a specific cognitive workflow. The structure of the request body depends on the `workflow_name`.
- **URL Parameter**: `workflow_name` (string) - The name of the workflow to run. Supported values: `system_id_workflow`, `control_tuning_workflow`.

##### Workflow: `system_id_workflow`

- **Request Body**: A `SystemIdWorkflowContext` JSON object. Note the special format for `bounds`.
  ```json
  {
    "data": [
      {"inflow": 10, "outflow": 9},
      {"inflow": 11, "outflow": 9.5}
    ],
    "model_type": "Muskingum",
    "dt": 1.0,
    "initial_guess": [10.0, 0.2],
    "bounds": [[0, 0], [100, 0.5]]
  }
  ```
- **Success Response**: The identified model parameters.
  ```json
  {
    "status": "success",
    "identified_parameters": {
      "K": 1.527,
      "X": 0.5
    },
    "goodness_of_fit": {
      "rmse": 0.04
    }
  }
  ```

##### Workflow: `control_tuning_workflow`

- **Request Body**: A `ControlTuningWorkflowContext` JSON object.
  ```json
  {
    "system_model": {
      "params": {
        "area": 100.0,
        "initial_level": 5.0,
        "max_level": 20.0
      }
    },
    "optimization_objective": "ISE",
    "parameter_bounds": [[0, 10], [0, 5], [0, 1]],
    "initial_guess": [0.5, 0.1, 0.01]
  }
  ```
- **Success Response**: The optimal controller parameters.
  ```json
  {
    "optimal_params": {
      "Kp": 0.0,
      "Ki": 0.0379,
      "Kd": 0.0
    },
    "final_cost": 627.87
  }
  ```
