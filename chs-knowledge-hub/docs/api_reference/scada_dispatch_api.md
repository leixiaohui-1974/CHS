# API Reference: SCADA Dispatch Service

The `chs-scada-dispatch` service is the cloud-native backend that acts as the central command and control center for the CHS platform. It provides RESTful and WebSocket APIs for data ingestion, monitoring, and dispatching high-level commands.

## Running the Service

To access the API, you first need to run the service. From the `chs-scada-dispatch` directory, run the following commands:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the FastAPI application
uvicorn app:app --host 0.0.0.0 --port 8001
```
*Note: We use port `8001` here to avoid conflicts with other services like the SDK service.*

## Interactive API Documentation

Once the service is running, you can access the interactive API documentation (provided by FastAPI's Swagger UI) by navigating to the following URL in your browser:

[**http://127.0.0.1:8001/docs**](http://127.0.0.1:8001/docs)

This interactive page allows you to see all available endpoints, their required parameters, and even send test requests directly from your browser.

## Key Endpoints

While the interactive documentation is the definitive source, here are some of the key conceptual endpoints you will find:

- **`POST /api/v1/data-ingestion/`**:
  - **Purpose**: Endpoint for `chs-edge` nodes to push time-series data (e.g., sensor readings).
  - **Payload**: Typically a JSON object containing device ID, timestamp, and key-value pairs of measurements.

- **`GET /api/v1/system-state/`**:
  - **Purpose**: Retrieves the last known state for all monitored devices.
  - **Response**: A JSON object mapping device IDs to their latest state data.

- **`GET /api/v1/alarms/`**:
  - **Purpose**: Fetches a list of currently active or historical alarms.
  - **Response**: A list of alarm objects, including severity, timestamp, and description.

- **`POST /api/v1/dispatch/command/`**:
  - **Purpose**: Sends a high-level command to a central control agent or directly to an edge node.
  - **Payload**: A JSON object describing the target device/agent and the command to be executed.

- **`WS /ws/v1/system-monitor/`**:
  - **Purpose**: A WebSocket endpoint that streams real-time system events, state changes, and new alarms to connected clients (like the `chs-hmi`).
