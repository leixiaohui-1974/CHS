from __future__ import annotations
import json
import logging
from typing import Any, Dict, TYPE_CHECKING

# NOTE: This agent requires the 'paho-mqtt' library.
# You can install it with: pip install paho-mqtt
try:
    import paho.mqtt.client as mqtt
except ImportError:
    # This allows the module to be imported even if paho-mqtt is not installed.
    # The agent will fail at runtime if instantiated, which is intended.
    mqtt = None

from ..agent.base_agent import BaseAgent

if TYPE_CHECKING:
    from ..agent.communication import MessageBus

logger = logging.getLogger(__name__)

class MqttHardwareProxy(BaseAgent):
    """
    An agent that acts as a proxy between the internal simulation's MessageBus
    and an external piece of hardware via MQTT. This is crucial for
    Hardware-in-the-Loop (HIL) simulations.
    """

    def __init__(self, id: str, message_bus: MessageBus, device_id: str, mqtt_broker: str, mqtt_port: int = 1883, **kwargs):
        super().__init__(id=id, message_bus=message_bus, **kwargs)
        if not mqtt:
            raise ImportError("paho-mqtt is not installed. Please install it to use MqttHardwareProxy.")

        self.device_id = device_id
        self.broker = mqtt_broker
        self.port = mqtt_port

        self.command_topic = f"chs/hil/{self.device_id}/command"
        self.state_topic = f"chs/hil/{self.device_id}/state"

        self.internal_command_topic = f"hardware.command.{self.device_id}"
        self.internal_state_topic = f"hardware.state.{self.device_id}"

        self._client = mqtt.Client(client_id=f"chs_sdk_proxy_{self.device_id}")
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

        self.message_bus.subscribe(self.internal_command_topic, self.handle_internal_command)
        logger.info(f"MqttHardwareProxy '{self.id}' initialized for device '{self.device_id}'.")

    def connect(self):
        """Connects to the MQTT broker."""
        logger.info(f"Connecting to MQTT broker at {self.broker}:{self.port}")
        try:
            self._client.connect(self.broker, self.port, 60)
            self._client.loop_start()
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}", exc_info=True)
            raise

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Successfully connected to MQTT broker.")
            client.subscribe(self.state_topic)
            logger.info(f"Subscribed to MQTT topic: {self.state_topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker, return code {rc}")

    def _on_message(self, client, userdata, msg):
        """Callback for when a message is received from the MQTT broker."""
        logger.debug(f"Received MQTT message on topic {msg.topic}")
        try:
            payload = json.loads(msg.payload.decode())
            self.message_bus.publish(self.internal_state_topic, payload, sender_id=self.id)
        except json.JSONDecodeError:
            logger.warning(f"Could not decode JSON from MQTT message: {msg.payload}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}", exc_info=True)

    def handle_internal_command(self, command: Dict[str, Any]):
        """Callback for when a command is received from the internal message bus."""
        logger.debug(f"Received internal command to send to hardware: {command}")
        try:
            payload = json.dumps(command)
            self._client.publish(self.command_topic, payload)
        except Exception as e:
            logger.error(f"Failed to publish command to MQTT: {e}", exc_info=True)

    def step(self, dt: float, **kwargs):
        """The proxy's step function is passive; all work is done in callbacks."""
        pass

    def disconnect(self):
        """Disconnects from the MQTT broker."""
        logger.info("Disconnecting from MQTT broker.")
        self._client.loop_stop()
        self._client.disconnect()

    def get_state(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.__class__.__name__,
            "device_id": self.device_id,
            "broker": self.broker,
            "port": self.port,
            "connected": self._client.is_connected() if self._client else False
        }
