import unittest
import numpy as np

# Adjust path to import SDK components
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'water_system_sdk', 'src')))

from water_system_simulator.modeling.instrument_models import LevelSensor, GateActuator

class TestInstrumentModels(unittest.TestCase):

    def test_level_sensor_initialization(self):
        sensor = LevelSensor(noise_std_dev=0.1)
        self.assertEqual(sensor.noise_std_dev, 0.1)
        self.assertEqual(sensor.measured_value, 0.0)

    def test_level_sensor_measure(self):
        true_level = 10.0
        sensor = LevelSensor(noise_std_dev=0.05)

        # After one step, the value should be different due to noise
        sensor.step(true_value=true_level)
        self.assertNotEqual(sensor.measured_value, true_level)
        self.assertEqual(sensor.measured_value, sensor.output)

        # Over many measurements, the mean should be close to the true value
        measurements = []
        for _ in range(1000):
            sensor.step(true_value=true_level)
            measurements.append(sensor.measured_value)
        mean_measured = np.mean(measurements)
        self.assertAlmostEqual(mean_measured, true_level, delta=0.05)

    def test_gate_actuator_initialization(self):
        actuator = GateActuator(travel_time=100.0, initial_position=0.5)
        self.assertEqual(actuator.travel_time, 100.0)
        self.assertEqual(actuator.current_position, 0.5)
        with self.assertRaises(ValueError):
            GateActuator(travel_time=0)

    def test_gate_actuator_step_movement(self):
        actuator = GateActuator(travel_time=100.0, initial_position=0.2)

        # Command to open further
        actuator.step(command=0.5, dt=1.0)
        # Max speed is 1.0 / 100.0 = 0.01 per second.
        # Expected position = 0.2 + 0.01 * 1.0 = 0.21
        self.assertAlmostEqual(actuator.current_position, 0.21)

        # Command to close
        actuator.step(command=0.1, dt=2.0)
        # Max change is 0.01 * 2.0 = 0.02
        # Required change is 0.1 - 0.21 = -0.11
        # Actual change is capped at -0.02
        # Expected position = 0.21 - 0.02 = 0.19
        self.assertAlmostEqual(actuator.current_position, 0.19)

    def test_gate_actuator_step_to_target(self):
        actuator = GateActuator(travel_time=100.0, initial_position=0.5)

        # Command is close, so it should reach the target exactly
        actuator.step(command=0.505, dt=1.0)
        # Max change is 0.01. Required change is 0.005.
        # Expected position = 0.5 + 0.005 = 0.505
        self.assertAlmostEqual(actuator.current_position, 0.505)

    def test_gate_actuator_clamping(self):
        actuator = GateActuator(travel_time=10.0, initial_position=0.95)

        # Command to open beyond 1.0
        actuator.step(command=1.5, dt=1.0)
        # Max speed is 1.0 / 10.0 = 0.1 per second.
        # Expected position = 0.95 + 0.1 = 1.05, which should be clamped to 1.0
        self.assertEqual(actuator.current_position, 1.0)

        # Command to close beyond 0.0
        actuator.current_position = 0.05
        actuator.step(command=-0.5, dt=1.0)
        # Expected position = 0.05 - 0.1 = -0.05, which should be clamped to 0.0
        self.assertEqual(actuator.current_position, 0.0)

if __name__ == '__main__':
    unittest.main()
