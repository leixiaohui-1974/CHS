import requests
import json
import time
import socketio
import unittest
import os

# --- Test Configuration ---
BASE_URL = "http://localhost:5001"
# A valid scenario config for the new dynamic gym_wrapper
SCENARIO_CONFIG = {
    "simulation_params": {
        "total_time": 10, # Short simulation for testing
        "dt": 1.0
    },
    "components": {
        "main_reservoir": {
            "type": "ReservoirModel",
            "params": {"area": 100.0, "initial_level": 10.0}
        }
    },
    "connections": [],
    "execution_order": ["main_reservoir"],
    "logger_config": ["main_reservoir.state.level"],
    "rl_config": {
        "observation_space": {
            "main_reservoir.state.level": {"low": 0, "high": 20}
        },
        "action_space": {
            "main_reservoir.input.inflow": {"low": 0, "high": 50}
        },
        "reward": [
            {
                "type": "distance_to_target",
                "variable": "main_reservoir.state.level",
                "target": 15.0,
                "weight": 1.0
            }
        ],
        "max_steps_per_episode": 10
    }
}

class TestE2EWorkflow(unittest.TestCase):

    def setUp(self):
        """Set up for the tests. Deletes the test database if it exists."""
        db_path = os.path.join(os.path.dirname(__file__), 'instance', 'projects.db')
        if os.path.exists(db_path):
            os.remove(db_path)
        # We assume the server is started separately for these tests.

    def test_full_workflow(self):
        """Tests the full user workflow from project creation to simulation."""

        # 1. Create a Project
        print("\n--- 1. Creating Project ---")
        create_payload = {
            "name": "E2E Test Project",
            "scenario": SCENARIO_CONFIG
        }
        response = requests.post(f"{BASE_URL}/api/projects", json=create_payload)
        self.assertEqual(response.status_code, 201)
        project_data = response.json()['project']
        project_id = project_data['id']
        print(f"Project created with ID: {project_id}")

        # 2. Get the project's topology
        print("\n--- 2. Fetching Topology ---")
        response = requests.get(f"{BASE_URL}/api/projects/{project_id}/topology")
        self.assertEqual(response.status_code, 200)
        topology_data = response.json()
        self.assertIn("components", topology_data)
        self.assertIn("main_reservoir", topology_data["components"])
        print("Topology fetched successfully.")

        # 3. Start a live simulation
        print("\n--- 3. Starting Live Simulation ---")
        response = requests.post(f"{BASE_URL}/api/projects/{project_id}/run_live")
        self.assertEqual(response.status_code, 200)
        sim_id = response.json()['simulation_id']
        self.assertIsNotNone(sim_id)
        print(f"Live simulation started with ID: {sim_id}")

        # 4. Connect to WebSocket and verify updates
        print("\n--- 4. Verifying WebSocket Updates ---")
        sio = socketio.Client(engineio_logger=True)
        update_received = False
        end_received = False

        @sio.on('connect', namespace='/live')
        def on_connect():
            print("Socket connected, joining room...")
            sio.emit('join_simulation_room', {'simulation_id': sim_id}, namespace='/live')

        @sio.on('simulation_update', namespace='/live')
        def on_update(data):
            nonlocal update_received
            update_received = True
            print(f"Received simulation update: {data}")
            self.assertIn("main_reservoir.state.level", data)

        @sio.on('simulation_end', namespace='/live')
        def on_end(data):
            nonlocal end_received
            end_received = True
            print("Received simulation end.")
            self.assertIn("results", data)

        try:
            sio.connect(BASE_URL, namespaces=['/live'], transports=['websocket'])
            # Wait long enough for the short simulation to complete
            sio.sleep(15)
        finally:
            sio.disconnect()

        self.assertTrue(update_received, "Did not receive any simulation updates via WebSocket.")
        self.assertTrue(end_received, "Did not receive the simulation end event via WebSocket.")
        print("WebSocket verification successful.")

if __name__ == '__main__':
    unittest.main()
