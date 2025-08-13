import unittest
import numpy as np

from water_system_simulator.modeling.control_structure_models import GateStationModel, PumpStationModel, HydropowerStationModel
from water_system_simulator.modeling.pipeline_model import PipelineModel

class TestNewModels(unittest.TestCase):

    def test_gate_station_model(self):
        """
        Tests the GateStationModel logic.
        """
        gate_configs = [
            {'discharge_coefficient': 0.6, 'area': 1.0},
            {'discharge_coefficient': 0.5, 'area': 1.0}
        ]

        station = GateStationModel(number_of_gates=2, gate_configs=gate_configs)

        upstream_level = 10.0
        downstream_level = 5.0
        areas = [1.5, 2.0] # Control inputs: area for each gate

        total_flow = station.step(upstream_level, downstream_level, areas)

        # Manually calculate the expected flow for each gate
        g = 9.81
        head_diff = upstream_level - downstream_level

        # Flow for gate 1
        flow1 = gate_configs[0]['discharge_coefficient'] * areas[0] * np.sqrt(2 * g * head_diff)

        # Flow for gate 2
        flow2 = gate_configs[1]['discharge_coefficient'] * areas[1] * np.sqrt(2 * g * head_diff)

        expected_total_flow = flow1 + flow2

        self.assertAlmostEqual(total_flow, expected_total_flow, places=5)
        self.assertAlmostEqual(station.output, expected_total_flow, places=5)
        print("\nGateStationModel test passed.")

    def test_pump_station_model(self):
        """
        Tests the PumpStationModel logic.
        """
        pump_configs = [
            {'max_flow': 10, 'max_head': 20},
            {'max_flow': 12, 'max_head': 25}
        ]

        station = PumpStationModel(number_of_pumps=2, pump_configs=pump_configs)

        head_diff = 10.0
        speeds = [0.8, 1.0]

        total_flow = station.step(head_diff, speeds)

        # Manually calculate expected flow
        flow1 = pump_configs[0]['max_flow'] * (1 - head_diff / pump_configs[0]['max_head']) * speeds[0]
        flow2 = pump_configs[1]['max_flow'] * (1 - head_diff / pump_configs[1]['max_head']) * speeds[1]
        expected_total_flow = flow1 + flow2

        self.assertAlmostEqual(total_flow, expected_total_flow, places=5)
        self.assertAlmostEqual(station.output, expected_total_flow, places=5)
        print("PumpStationModel test passed.")

    def test_pipeline_model_acceleration(self):
        """
        Tests the PipelineModel's inertial properties without friction.
        """
        pipe = PipelineModel(length=1000, diameter=1, friction_factor=0, initial_flow=0)

        inlet_pressure = 10.0 # 10m of head
        outlet_pressure = 0.0
        dt = 1.0

        # After one time step
        pipe.step(inlet_pressure, outlet_pressure, dt)

        # Expected acceleration: a = g*h/L = 9.81 * 10 / 1000 = 0.0981 m/s^2
        expected_velocity = 0.0981 * dt
        expected_flow = expected_velocity * pipe.area

        self.assertAlmostEqual(pipe.output, expected_flow, places=5)
        print("PipelineModel acceleration test passed.")

    def test_hydropower_station_model(self):
        """
        Tests the HydropowerStationModel logic for flow and power calculation.
        """
        station = HydropowerStationModel(rated_flow=100, rated_head=50, efficiency=0.9)

        upstream_level = 100.0
        downstream_level = 50.0 # This gives a head_diff equal to the rated head
        guide_vane_opening = 0.8

        flow = station.step(upstream_level, downstream_level, guide_vane_opening)

        # Expected flow
        head_diff = upstream_level - downstream_level
        expected_flow_coeff = 100 / np.sqrt(50)
        expected_flow = expected_flow_coeff * guide_vane_opening * np.sqrt(head_diff)

        # Expected power (in MW)
        expected_power = 0.9 * 1000 * 9.81 * expected_flow * head_diff / 1e6

        self.assertAlmostEqual(flow, expected_flow, places=5)
        self.assertAlmostEqual(station.power_generation, expected_power, places=5)
        print("HydropowerStationModel test passed.")

    def run_engine_test(self, config_file):
        """Helper function to run a simple engine test."""
        from water_system_simulator.engine import Simulator
        try:
            sim = Simulator(f"configs/{config_file}")
            sim.run(duration=1, dt=1, log_file=f"test_{config_file}.csv")
            return True
        except Exception as e:
            print(f"Engine test failed for {config_file}: {e}")
            return False

    def test_engine_integration(self):
        """
        Tests the integration of new models with the simulation engine.
        """
        print("\n--- Running Engine Integration Tests ---")
        test_configs = [
            "test_gate_station_topology.yml",
            "test_pump_station_topology.yml",
            "test_pipeline_model_topology.yml",
            "test_hydropower_station_topology.yml"
        ]

        for config in test_configs:
            with self.subTest(config=config):
                self.assertTrue(self.run_engine_test(config), f"Engine test failed for {config}")

        print("All engine integration tests passed.")


if __name__ == '__main__':
    unittest.main()
