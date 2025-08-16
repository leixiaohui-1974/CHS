import paho.mqtt.client as mqtt
import time
import threading
import json
import logging
from drivers.hardware_interface import MockHardware


class MqttService:
    """
    Handles MQTT communication for the edge device.
    """
    def __init__(self, hardware: MockHardware, device_id: str = 'device01', broker_address: str = 'localhost', port: int = 1883):
        """
        Initializes the MqttService.

        Args:
            hardware: An instance of a hardware interface for reading sensor data.
            device_id: The unique identifier for this edge device.
            broker_address: The address of the MQTT broker.
            port: The port of the MQTT broker.
        """
        self.hardware = hardware
        self.device_id = device_id
        self.broker_address = broker_address
        self.port = port

        self.command_topic = f"chs/edge/{self.device_id}/command"
        self.state_topic = f"chs/edge/{self.device_id}/state"

        self.client = mqtt.Client(client_id=f"chs_edge_{device_id}")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker."""
        if rc == 0:
            logging.info("Connected to MQTT Broker!")
            self.client.subscribe(self.command_topic)
            logging.info(f"Subscribed to topic: {self.command_topic}")
        else:
            logging.error(f"Failed to connect to MQTT Broker, return code {rc}")

    def on_message(self, client, userdata, msg):
        """Callback for when a message is received from the broker."""
        logging.info(f"Received command on topic {msg.topic}: {msg.payload.decode()}")

    def _publish_state_loop(self):
        """The loop that periodically publishes the device's state."""
        while True:
            state = self.hardware.read_sensors()
            payload = json.dumps(state)
            self.client.publish(self.state_topic, payload)
            logging.info(f"[MQTT] Published state to {self.state_topic}: {payload}")
            time.sleep(5)

    def run(self):
        """Connects to the MQTT broker and starts the service's background threads."""
        try:
            self.client.connect(self.broker_address, self.port, 60)
            self.client.loop_start()  # Handles network traffic in a background thread

            publish_thread = threading.Thread(target=self._publish_state_loop, name="MqttPublishThread")
            publish_thread.daemon = True  # Allows main program to exit even if thread is running
            publish_thread.start()
            logging.info("MQTT service started.")
        except ConnectionRefusedError:
            logging.error(f"MQTT connection refused. Is a broker running at {self.broker_address}:{self.port}?")
        except Exception as e:
            logging.error(f"An error occurred while starting MQTT service: {e}", exc_info=True)


    def stop(self):
        """Stops the MQTT service and disconnects the client."""
        self.client.loop_stop()
        self.client.disconnect()
        logging.info("MQTT service stopped.")
