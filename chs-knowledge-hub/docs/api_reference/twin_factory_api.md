# API Reference: Twin Factory Service

The `chs-twin-factory` service is the MLOps platform for the CHS ecosystem. It provides an API for managing the lifecycle of AI agents, including training, evaluation, and packaging. A key feature is its ability to wrap CHS simulations as standard Gymnasium environments.

## Running the Service

To access the API, you first need to run the service. From the `chs-twin-factory/backend` directory, run the following commands:

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations (if you have a database configured)
# alembic upgrade head

# Run the FastAPI application
uvicorn app:app --host 0.0.0.0 --port 8002
```
*Note: We use port `8002` here to avoid conflicts with other services.*

## Interactive API Documentation

Once the service is running, you can access the interactive API documentation (provided by FastAPI's Swagger UI) by navigating to the following URL in your browser:

[**http://127.0.0.1:8002/docs**](http://127.0.0.1:8002/docs)

This interactive page allows you to see all available endpoints and test them directly.

## Key Endpoints

The Twin Factory API is centered around the concepts of environments, experiments, and agent training jobs.

- **`POST /api/v1/experiments/`**:
  - **Purpose**: Creates a new training experiment.
  - **Payload**: A JSON object containing the simulation configuration to wrap as a Gym environment, the RL algorithm to use (e.g., "PPO", "SAC"), and hyperparameters.

- **`GET /api/v1/experiments/{experiment_id}`**:
  - **Purpose**: Retrieves the status and results of a specific experiment.
  - **Response**: A JSON object with details about the experiment, including training progress, rewards, and links to saved models.

- **`POST /api/v1/experiments/{experiment_id}/run`**:
  - **Purpose**: Starts the training job for a created experiment.

- **`GET /api/v1/agents/`**:
  - **Purpose**: Lists all trained and packaged agents that are ready for deployment.
  - **Response**: A list of agent objects with names, versions, and performance metrics.

- **`GET /api/v1/agents/{agent_id}/package`**:
  - **Purpose**: Downloads the packaged `.agent` file for a trained agent, which can then be deployed to a `chs-edge` or `chs-scada-dispatch` node.
