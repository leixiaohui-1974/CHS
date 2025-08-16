import requests
import json
import time
import subprocess
import os
import sys

# --- 1. Start the backend server ---
print("Starting backend server...")
python_executable = sys.executable
# Running app.py from its directory is safer for relative paths
server_process = subprocess.Popen(
    [python_executable, 'app.py'],
    cwd='chs-twin-factory/backend/',
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
# Give the server time to start up and initialize the database
time.sleep(10)

BASE_URL = 'http://127.0.0.1:5001'
model_filename = None

try:
    # --- 2. Create a project ---
    print("Creating a new project...")
    # This scenario is for the new CHS_SDK used by the gym_wrapper
    scenario = {
        "components": [
            {
                "id": "R1", "type": "Reservoir",
                "params": { "initial_level": 90, "max_level": 100, "min_level": 80, "area": 1000 }
            },
            {
                "id": "T1", "type": "Turbine",
                "params": { "max_flow": 100 }
            }
        ],
        "connections": [
            {"from": "R1", "to": "T1"}
        ],
        "control": [
            { "component_id": "T1", "variable": "outflow" }
        ]
    }
    project_data = {
        "name": "Test RL Project",
        "scenario": scenario
    }
    response = requests.post(f"{BASE_URL}/api/projects", json=project_data)
    response.raise_for_status()
    project = response.json()['project']
    project_id = project['id']
    print(f"Project created with ID: {project_id}")

    # --- 3. Start training ---
    print("Starting training... (This may take a minute or two)")
    train_params = {
        "algorithm": "PPO",
        "total_timesteps": 256 # very short, but enough for SB3 to initialize and save
    }
    # This is a blocking call and might take a while, so we use a generous timeout
    response = requests.post(f"{BASE_URL}/api/projects/{project_id}/train", json=train_params, timeout=180)
    response.raise_for_status()
    train_result = response.json()
    print("Training complete:", train_result)
    assert train_result['status'] == 'success'

    # --- 4. Check for the model ---
    print("Fetching models for the project...")
    response = requests.get(f"{BASE_URL}/api/projects/{project_id}/models")
    response.raise_for_status()
    models = response.json()
    print(f"Found models: {models}")
    assert len(models) > 0
    model_id = models[0]['id']

    # --- 5. Download the model ---
    print(f"Downloading model with ID: {model_id}...")
    response = requests.get(f"{BASE_URL}/api/models/{model_id}", stream=True)
    response.raise_for_status()

    model_filename = f"test_model_{model_id}.zip"
    with open(model_filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"Model saved to {model_filename}")
    # Check if the file is a non-empty zip file
    assert os.path.getsize(model_filename) > 100

    print("\n--- Test workflow successful! ---")

except Exception as e:
    print(f"\n--- Test failed: An unexpected error occurred: {e} ---", file=sys.stderr)
    # Give a moment for any final output from the server
    time.sleep(1)
    # Now terminate and get output
    server_process.terminate()
    stdout, stderr = server_process.communicate()
    print("--- Server STDOUT ---", file=sys.stderr)
    print(stdout, file=sys.stderr)
    print("--- Server STDERR ---", file=sys.stderr)
    print(stderr, file=sys.stderr)
    sys.exit(1) # Exit with error

finally:
    # --- 6. Clean up ---
    print("Stopping backend server...")
    server_process.terminate()
    server_process.wait()
    # Clean up the downloaded file
    if model_filename and os.path.exists(model_filename):
        os.remove(model_filename)
        print(f"Cleaned up {model_filename}")
