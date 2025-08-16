import paho.mqtt.client as mqtt
import json
import logging
from data_processing.timeseries_db import TimeSeriesDB
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MqttService:
    """
    Connects to an MQTT broker to subscribe to device state topics
    and publish commands to edge devices.
    """
    def __init__(self, timeseries_db: TimeSeriesDB, broker_address="localhost", port=1883):
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self._timeseries_db = timeseries_db
        self._broker_address = broker_address
        self._port = port
        self._subscribe_topic = "chs/edge/+/state"
        self._command_topic_template = "chs/edge/{device_id}/command"
        self._config_topic_template = "chs/edge/{device_id}/config/update"

        # Assign callbacks
        self._client.on_connect = self.on_connect
        self._client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        """The callback for when the client receives a CONNACK response from the server."""
        if rc == 0:
            logging.info("Connected to MQTT Broker!")
            client.subscribe(self._subscribe_topic)
            logging.info(f"Subscribed to topic: {self._subscribe_topic}")
        else:
            logging.error(f"Failed to connect, return code {rc}")

    def on_message(self, client, userdata, msg):
        """The callback for when a PUBLISH message is received from the server."""
        try:
            payload = msg.payload.decode()
            logging.info(f"Received message on topic {msg.topic}: {payload}")
            data = json.loads(payload)

            # Extract device_id from the topic
            topic_parts = msg.topic.split('/')
            if len(topic_parts) == 4 and topic_parts[0] == 'chs' and topic_parts[1] == 'edge' and topic_parts[3] == 'state':
                device_id = topic_parts[2]
                self._timeseries_db.write_device_status(device_id, data)
                logging.info(f"Wrote status to InfluxDB for device: {device_id}")
            else:
                logging.warning(f"Received message on unexpected topic structure: {msg.topic}")

        except json.JSONDecodeError:
            logging.error(f"Failed to decode JSON from message: {msg.payload.decode()}")
        except Exception as e:
            logging.error(f"An error occurred in on_message: {e}")

    def publish_command(self, device_id: str, command: Dict[str, Any]):
        """Publishes a command to a specific device's command topic."""
        try:
            topic = self._command_topic_template.format(device_id=device_id)
            payload = json.dumps(command)
            result = self._client.publish(topic, payload)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logging.info(f"Successfully published command to topic {topic}: {payload}")
            else:
                logging.error(f"Failed to publish command to topic {topic}. Return code: {result.rc}")
        except Exception as e:
            logging.error(f"An error occurred while publishing command for device {device_id}: {e}")

    def publish_config(self, device_id: str, config_data: Dict[str, Any]):
        """Publishes a configuration update to a specific device."""
        try:
            topic = self._config_topic_template.format(device_id=device_id)
            payload = json.dumps(config_data)
            result = self._client.publish(topic, payload, qos=1) # Use QoS 1 for reliability

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logging.info(f"Successfully published config update to topic {topic}: {payload}")
            else:
                logging.error(f"Failed to publish config to topic {topic}. Return code: {result.rc}")
        except Exception as e:
            logging.error(f"An error occurred while publishing config for device {device_id}: {e}")

    def start(self):
        """Connects to the broker and starts the network loop."""
        try:
            self._client.connect(self._broker_address, self._port, 60)
            self._client.loop_start()
            logging.info(f"MQTT Service started, connected to {self._broker_address}:{self._port}")
        except ConnectionRefusedError:
            logging.error(f"Connection to MQTT broker at {self._broker_address}:{self._port} was refused.")
        except Exception as e:
            logging.error(f"Failed to start MQTT service: {e}")

    def stop(self):
        """Stops the MQTT client loop."""
        self._client.loop_stop()
        logging.info("MQTT Service stopped.")
