import paho.mqtt.client as mqtt
import json
import logging
from data_processing.status_store import StatusStore

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MqttConsumer:
    """
    Connects to an MQTT broker, subscribes to a topic, and updates a status store.
    """
    def __init__(self, status_store: StatusStore, broker_address="localhost", port=1883):
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self._status_store = status_store
        self._broker_address = broker_address
        self._port = port
        self._topic = "chs/edge/+/state"

        # Assign callbacks
        self._client.on_connect = self.on_connect
        self._client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        """The callback for when the client receives a CONNACK response from the server."""
        if rc == 0:
            logging.info("Connected to MQTT Broker!")
            client.subscribe(self._topic)
            logging.info(f"Subscribed to topic: {self._topic}")
        else:
            logging.error(f"Failed to connect, return code {rc}")

    def on_message(self, client, userdata, msg):
        """The callback for when a PUBLISH message is received from the server."""
        try:
            payload = msg.payload.decode()
            logging.info(f"Received message on topic {msg.topic}: {payload}")
            data = json.loads(payload)

            # Extract device_id from the topic, e.g., chs/edge/pump_station_01/state
            topic_parts = msg.topic.split('/')
            if len(topic_parts) == 4 and topic_parts[0] == 'chs' and topic_parts[1] == 'edge' and topic_parts[3] == 'state':
                device_id = topic_parts[2]
                self._status_store.update_device_status(device_id, data)
                logging.info(f"Updated status for device: {device_id}")
            else:
                logging.warning(f"Received message on unexpected topic structure: {msg.topic}")

        except json.JSONDecodeError:
            logging.error(f"Failed to decode JSON from message: {msg.payload.decode()}")
        except Exception as e:
            logging.error(f"An error occurred in on_message: {e}")

    def start(self):
        """Connects to the broker and starts the network loop."""
        try:
            self._client.connect(self._broker_address, self._port, 60)
            # loop_start() runs the client loop in a background thread.
            self._client.loop_start()
            logging.info(f"MQTT Consumer started, connected to {self._broker_address}:{self._port}")
        except ConnectionRefusedError:
            logging.error(f"Connection to MQTT broker at {self._broker_address}:{self._port} was refused. Make sure a broker is running.")
        except Exception as e:
            logging.error(f"Failed to start MQTT consumer: {e}")

    def stop(self):
        """Stops the MQTT client loop."""
        self._client.loop_stop()
        logging.info("MQTT Consumer stopped.")
