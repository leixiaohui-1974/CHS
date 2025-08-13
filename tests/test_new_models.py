import unittest
import os
import shutil
import yaml
from water_system_simulator.simulation_manager import SimulationManager

class TestNewModelIntegration(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory for test case files."""
        self.test_dir = "temp_test_case"
        os.makedirs(self.test_dir, exist_ok=True)
        self.results_dir = "results"
        os.makedirs(self.results_dir, exist_ok=True)


    def tearDown(self):
        """Clean up the temporary directory and results."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        # Clean up any results files generated during tests
        for f in os.listdir(self.results_dir):
            if f.startswith("test_case_"):
                os.remove(os.path.join(self.results_dir, f))

    def _run_simulation_test(self, config, log_prefix):
        """Helper to run a simulation and check for basic success."""
        topology_path = os.path.join(self.test_dir, 'topology.yml')
        with open(topology_path, 'w') as f:
            yaml.dump(config, f)

        # Create a dummy disturbances file, as the manager expects it
        disturbance_path = os.path.join(self.test_dir, 'disturbances.csv')
        with open(disturbance_path, 'w', newline='') as f:
            f.write("time,dummy\n0,0\n")

        # Create a dummy control parameters file
        control_params_path = os.path.join(self.test_dir, 'control_parameters.yaml')
        with open(control_params_path, 'w') as f:
            f.write("# No control params needed for these tests\n")

        try:
            manager = SimulationManager(self.test_dir)
            manager.run(duration=config.get('duration', 10), log_file_prefix=log_prefix)
        except Exception as e:
            self.fail(f"Simulation for {log_prefix} failed with an exception: {e}")

        log_path = os.path.join(self.results_dir, f"{log_prefix}_log.csv")
        self.assertTrue(os.path.exists(log_path), f"Log file for {log_prefix} should be created.")

    def test_pipeline_model(self):
        config = {
            'dt': 1.0, 'solver': 'EulerIntegrator',
            'components': [
                {'name': 'r_up', 'type': 'ConstantHeadReservoir', 'properties': {'level': 100.0}},
                {'name': 'r_down', 'type': 'ConstantHeadReservoir', 'properties': {'level': 90.0}},
                {'name': 'p1', 'type': 'PipelineModel',
                 'properties': {'length': 1000.0, 'diameter': 0.5, 'friction_factor': 0.02},
                 'connections': {'inlet_pressure': 'r_up.output', 'outlet_pressure': 'r_down.output', 'dt': 1.0}}
            ],
            'logging': ['time', 'p1.flow']
        }
        self._run_simulation_test(config, "test_case_pipeline")

    def test_gate_station_model(self):
        config = {
            'dt': 1.0, 'solver': 'EulerIntegrator',
            'components': [
                {'name': 'g1', 'type': 'GateStationModel',
                 'properties': {'num_gates': 2, 'gate_width': 1.5, 'discharge_coeff': 0.6},
                 'connections': {'upstream_level': 10.0, 'gate_opening': 0.5}}
            ],
            'logging': ['time', 'g1.flow']
        }
        self._run_simulation_test(config, "test_case_gate")

    def test_pump_station_model(self):
        config = {
            'dt': 1.0, 'solver': 'EulerIntegrator',
            'components': [
                {'name': 'ps1', 'type': 'PumpStationModel',
                 'properties': {'num_pumps_total': 3, 'curve_coeffs': [-0.01, 0.1, 5.0]},
                 'connections': {'inlet_pressure': 5.0, 'outlet_pressure': 20.0, 'num_pumps_on': 2}}
            ],
            'logging': ['time', 'ps1.flow']
        }
        self._run_simulation_test(config, "test_case_pump")

    def test_hydropower_station_model(self):
        config = {
            'dt': 1.0, 'solver': 'EulerIntegrator',
            'components': [
                {'name': 'hs1', 'type': 'HydropowerStationModel',
                 'properties': {'max_flow_area': 10.0, 'discharge_coeff': 0.8, 'efficiency': 0.9},
                 'connections': {'upstream_level': 150.0, 'downstream_level': 100.0, 'vane_opening': 0.75}}
            ],
            'logging': ['time', 'hs1.flow', 'hs1.power']
        }
        self._run_simulation_test(config, "test_case_hydropower")

if __name__ == '__main__':
    unittest.main()
