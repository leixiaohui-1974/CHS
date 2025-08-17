from fastapi import FastAPI
from typing import Dict, Any
import pandas as pd

# This path adjustment is for running the service locally for development.
# It allows the service to find the 'src' package.
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.chs_sdk.simulation_manager import SimulationManager

app = FastAPI(
    title="CHS Water System Simulator API",
    description="An API to run simulations for the CHS Water System.",
    version="0.1.0",
)

@app.post("/run_simulation/")
async def run_simulation(config: Dict[str, Any]):
    """
    Run a simulation based on a provided configuration dictionary.

    This endpoint accepts the same configuration format that the
    SimulationManager expects. The configuration should be sent as a
    JSON object in the request body.
    """
    try:
        print("--- Initializing SimulationManager from API request ---")
        manager = SimulationManager(config=config)

        print("--- Running simulation ---")
        results_df = manager.run()

        print("--- Simulation finished. Returning results. ---")

        # Convert DataFrame to a JSON-friendly format (list of records)
        results_dict = results_df.to_dict(orient='records')

        return {
            "status": "success",
            "data": results_dict
        }
    except Exception as e:
        # In a production environment, you'd want more robust error handling
        # and logging. You might also want to return proper HTTP status codes.
        return {
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }

@app.get("/")
async def root():
    """
    Root endpoint for the API.
    """
    return {
        "message": "Welcome to the CHS Water System Simulator API.",
        "docs_url": "/docs"
    }
