import os
import json
import unittest
from app import app, db, Project

class ProjectAPITestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        # Use an in-memory SQLite database for testing
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_create_and_get_project(self):
        # 1. Test creating a new project
        scenario = {
            "components": {
                "reservoir": {"initial_level": 10.0, "area_storage_curve_coeff": 1000.0},
                "sluice_gate": {"width": 5.0},
            },
            "controller": {"target_level": 12.0},
            "simulation_params": {"duration_hours": 1},
        }
        create_response = self.client.post('/api/projects',
                                           data=json.dumps({"name": "Test Project", "scenario": scenario}),
                                           content_type='application/json')
        self.assertEqual(create_response.status_code, 201)
        create_data = create_response.get_json()
        self.assertEqual(create_data['status'], 'success')
        self.assertEqual(create_data['project']['name'], 'Test Project')
        project_id = create_data['project']['id']

        # 2. Test getting the list of projects
        list_response = self.client.get('/api/projects')
        self.assertEqual(list_response.status_code, 200)
        list_data = list_response.get_json()
        self.assertEqual(len(list_data), 1)
        self.assertEqual(list_data[0]['name'], 'Test Project')

        # 3. Test getting a single project
        single_response = self.client.get(f'/api/projects/{project_id}')
        self.assertEqual(single_response.status_code, 200)
        single_data = single_response.get_json()
        self.assertEqual(single_data['name'], 'Test Project')
        self.assertEqual(single_data['scenario']['controller']['target_level'], 12.0)

    def test_run_simulation_for_project(self):
        # First, create a project to run
        scenario = {
            "components": {
                "reservoir": {"initial_level": 10.0, "area_storage_curve_coeff": 1000.0},
                "sluice_gate": {"width": 5.0},
            },
            "controller": {"target_level": 12.0},
            "simulation_params": {"duration_hours": 0.01}, # Use a short duration for testing
        }
        create_response = self.client.post('/api/projects',
                                           data=json.dumps({"name": "Runnable Project", "scenario": scenario}),
                                           content_type='application/json')
        project_id = create_response.get_json()['project']['id']

        # 4. Test running a simulation for the project
        run_response = self.client.post(f'/api/projects/{project_id}/run')
        self.assertEqual(run_response.status_code, 200)
        run_data = run_response.get_json()
        self.assertEqual(run_data['status'], 'success')
        self.assertIn('time', run_data['data'])
        self.assertIn('level', run_data['data'])
        self.assertTrue(len(run_data['data']['time']) > 0)

        # 5. Test getting the simulation runs for the project
        runs_response = self.client.get(f'/api/projects/{project_id}/runs')
        self.assertEqual(runs_response.status_code, 200)
        runs_data = runs_response.get_json()
        self.assertEqual(len(runs_data), 1)
        self.assertIn('results', runs_data[0])
        self.assertIn('level', runs_data[0]['results'])

if __name__ == '__main__':
    unittest.main()
