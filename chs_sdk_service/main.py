from fastapi import FastAPI, Body, HTTPException
from typing import Any, Dict
import pandas as pd

from .models import (
    ScenarioConfig,
    SystemIdWorkflowContext,
    ControlTuningWorkflowContext,
)
from .launcher_util import run_simulation_and_capture_data
from chs_sdk.factory.mother_machine import MotherMachine

app = FastAPI(
    title="CHS-SDK Service",
    description="A REST API to expose the core functionalities of the CHS-SDK, including simulation and cognitive workflows.",
    version="1.0.0"
)

# ======================================================================================
# System Endpoints
# ======================================================================================

@app.get("/health", tags=["System"])
def health_check():
    """
    Checks if the service is running and healthy.
    """
    return {"status": "ok"}

# ======================================================================================
# API V1 Endpoints
# ======================================================================================

API_V1_PREFIX = "/api/v1"

@app.post(f"{API_V1_PREFIX}/run_simulation", tags=["Simulation"])
def run_simulation(scenario_config: ScenarioConfig):
    """
    Runs a complete simulation scenario based on a provided configuration.

    This endpoint dynamically injects a data capture agent into the simulation
    to record all message traffic and returns it as the result.
    """
    try:
        simulation_results = run_simulation_and_capture_data(scenario_config)
        return {"data": simulation_results}
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.post(f"{API_V1_PREFIX}/run_workflow/{{workflow_name}}", tags=["Workflows"])
async def run_workflow(workflow_name: str, context: Dict[str, Any] = Body(...)):
    """
    Executes a cognitive or optimization workflow using the MotherMachine.

    The structure of the `context` in the request body depends on the `workflow_name`.

    - **For `system_id_workflow`**: Provide `SystemIdWorkflowContext`.
    - **For `control_tuning_workflow`**: Provide `ControlTuningWorkflowContext`.
    """
    mother_machine = MotherMachine()

    try:
        # Validate and prepare the context based on the workflow name
        if workflow_name == "system_id_workflow":
            validated_context = SystemIdWorkflowContext.parse_obj(context)
            # The workflow expects a pandas DataFrame, so we convert it.
            workflow_payload = validated_context.dict()
            workflow_payload['data'] = pd.DataFrame(workflow_payload['data'])

        elif workflow_name == "control_tuning_workflow":
            validated_context = ControlTuningWorkflowContext.parse_obj(context)
            workflow_payload = validated_context.dict()

        else:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow '{workflow_name}' not found or not supported."
            )

        # Run the workflow
        result = mother_machine.run_workflow(workflow_name, workflow_payload)

        # Clean up non-serializable parts of the result for the API response
        if workflow_name == "control_tuning_workflow" and "optimizer_result" in result:
            # Convert numpy types to standard Python types
            if "optimal_params" in result:
                result["optimal_params"] = {k: float(v) for k, v in result["optimal_params"].items()}
            if "final_cost" in result:
                result["final_cost"] = float(result["final_cost"])

            # Remove the non-serializable Scipy OptimizeResult object
            del result["optimizer_result"]

        return result

    except ImportError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (ValueError, TypeError) as e:
        # Pydantic validation errors or other type errors
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred in the workflow: {e}")
