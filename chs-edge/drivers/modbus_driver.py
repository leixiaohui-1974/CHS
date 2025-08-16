import logging
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ConnectionException

class ModbusHardware:
    """
    Hardware interface for a device that communicates over Modbus TCP.
    """
    def __init__(self, ip: str, port: int, sensor_addr: int, actuator_addr: int):
        """
        Initializes the ModbusHardware.

        Args:
            ip: The IP address of the PLC.
            port: The port for the Modbus TCP connection.
            sensor_addr: The starting register address for sensor readings.
            actuator_addr: The starting register address for actuator commands.
        """
        self.client = ModbusTcpClient(ip, port=port)
        self.sensor_address = sensor_addr
        self.actuator_address = actuator_addr
        self.connect()

    def connect(self):
        """Connects to the Modbus server."""
        if not self.client.connect():
            logging.error(f"Failed to connect to Modbus server at {self.client.host}:{self.client.port}")
            raise ConnectionException("Modbus connection failed")
        logging.info(f"Successfully connected to Modbus server at {self.client.host}:{self.client.port}")

    def read_sensors(self) -> dict:
        """
        Reads sensor data from the configured Modbus register.
        Assumes the sensor value is a single floating-point number (2 registers).
        """
        try:
            # Reading a 32-bit float may require reading 2x 16-bit registers.
            # This is a simplified example assuming we read one holding register.
            rr = self.client.read_holding_registers(self.sensor_address, 1)
            if rr.isError():
                logging.error(f"Modbus Error: {rr}")
                return {}

            # This is a placeholder for actual data conversion
            sensor_value = rr.registers[0]

            observation = {
                'current_level': sensor_value,
                'dt': 1.0
            }
            logging.info(f"Reading sensors via Modbus: {observation}")
            return observation
        except Exception as e:
            logging.error(f"Error reading from Modbus: {e}")
            return {}

    def write_actuators(self, action: dict):
        """
        Writes an action to the configured Modbus register.
        """
        try:
            gate_opening = action.get('gate_opening', 0)
            # This is a placeholder for actual data conversion
            register_value = int(gate_opening)

            wq = self.client.write_register(self.actuator_address, register_value)
            if wq.isError():
                 logging.error(f"Modbus Error: {wq}")
            else:
                logging.info(f"Writing to actuators via Modbus: {action}")
        except Exception as e:
            logging.error(f"Error writing to Modbus: {e}")

    def __del__(self):
        """Ensures the client connection is closed upon object destruction."""
        if self.client.is_socket_open():
            self.client.close()
            logging.info("Modbus connection closed.")
