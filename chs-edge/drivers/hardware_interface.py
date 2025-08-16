import logging
import numpy as np
from drivers.modbus_driver import ModbusHardware

class MockHardware:
    """
    A mock hardware interface that simulates interaction with real-world
    sensors and actuators. This is used for SIL (Software-in-the-Loop) testing.
    """
    def __init__(self):
        """Initializes the mock hardware with a starting state."""
        self.current_level = 20.0
        logging.info("MockHardware initialized with starting level: %.2f", self.current_level)

    def read_sensors(self) -> dict:
        """
        Simulates reading sensor data.
        In this mock, it returns a fluctuating water level.
        """
        # Simulate a slight random fluctuation around the current level
        self.current_level += np.random.normal(0, 0.05)

        # Simulate a slow drift (e.g., a constant small inflow)
        self.current_level += 0.01

        observation = {
            'current_level': self.current_level,
            'dt': 1.0  # Assume a 1-second time step for control
        }
        logging.info(f"[MOCK] Reading sensors: {observation}")
        return observation

    def write_actuators(self, action: dict):
        """
        Simulates sending commands to actuators (e.g., a gate).
        In this mock, it adjusts the water level based on the action.
        """
        logging.info(f"[MOCK] Writing to actuators: {action}")

        # Example logic: if a 'gate_opening' action is received, it affects the level.
        # A larger opening causes the level to drop.
        gate_opening = action.get('gate_opening', 0.0)

        # Simulate outflow based on gate opening
        outflow_effect = gate_opening * 0.1
        self.current_level -= outflow_effect

        logging.info(f"[MOCK] Actuator action resulted in new level: {self.current_level:.2f}")

def get_hardware_interface(config: dict):
    """
    Factory function to get the appropriate hardware interface based on configuration.

    Args:
        config: A dictionary containing the application configuration.

    Returns:
        An instance of a hardware interface (e.g., MockHardware, ModbusHardware).
    """
    protocol = config.get('HARDWARE_PROTOCOL', 'mock').lower()
    logging.info(f"Selected hardware protocol: {protocol}")

    if protocol == 'modbus_tcp':
        try:
            return ModbusHardware(
                ip=config['PLC_IP_ADDRESS'],
                port=int(config['PLC_PORT']),
                sensor_addr=int(config['SENSOR_REGISTER_ADDRESS']),
                actuator_addr=int(config['ACTUATOR_REGISTER_ADDRESS'])
            )
        except Exception as e:
            logging.error(f"Failed to initialize ModbusHardware, falling back to MockHardware. Error: {e}")
            return MockHardware()
    elif protocol == 'mock':
        return MockHardware()
    else:
        logging.warning(f"Unknown hardware protocol '{protocol}'. Falling back to MockHardware.")
        return MockHardware()
