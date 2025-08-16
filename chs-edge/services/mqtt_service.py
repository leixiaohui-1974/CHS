import paho.mqtt.client as mqtt
import time
import threading
import json
import logging
import requests
import os
from engine.executor import Executor

class MqttService:
    """
    Handles MQTT communication for the edge device, including command and control.
    """
    def __init__(self, executor: Executor, config: dict):
        """
        Initializes the MqttService.

        Args:
            executor: The agent executor instance.
            config: A dictionary containing the application configuration.
        """
        self.executor = executor
        self.device_id = config['DEVICE_ID']
        self.broker_address = config['MQTT_BROKER_ADDRESS']
        self.port = int(config['MQTT_PORT'])

        self.command_topic = f"chs/edge/{self.device_id}/command"
        self.state_topic = f"chs/edge/{self.device_id}/state"
        self.notify_topic = f"chs/edge/{self.device_id}/notify"

        self.client = mqtt.Client(client_id=f"chs_edge_{self.device_id}")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker."""
        if rc == 0:
            logging.info("Connected to MQTT Broker!")
            self.client.subscribe(self.command_topic)
            logging.info(f"Subscribed to topic: {self.command_topic}")
        else:
            logging.error(f"Failed to connect, return code {rc}")

    def on_message(self, client, userdata, msg):
        """Callback for when a command is received."""
        try:
            payload = msg.payload.decode()
            logging.info(f"Received command on topic {msg.topic}: {payload}")
            command = json.loads(payload)
            self.handle_command(command)
        except json.JSONDecodeError:
            logging.error("Failed to decode JSON from command payload.")
        except Exception as e:
            logging.error(f"Error processing command: {e}")

    def handle_command(self, command: dict):
        """Handles the logic for different command types."""
        command_type = command.get('type')
        if command_type == 'update_model':
            self.handle_update_model(command)
        elif command_type == 'change_param':
            self.handle_change_param(command)
        else:
            logging.warning(f"Unknown command type: {command_type}")

    def handle_update_model(self, command: dict):
        """Handles downloading and reloading a new agent model."""
        url = command.get('url')
        if not url:
            logging.error("'update_model' command missing 'url' field.")
            return

        try:
            logging.info(f"Downloading new model from {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Save the new agent file, overwriting the old one.
            new_model_path = self.executor.model_path
            with open(new_model_path, 'wb') as f:
                f.write(response.content)

            logging.info(f"New model saved to {new_model_path}")

            # Trigger the executor to reload the agent
            success = self.executor.reload_agent(new_model_path)
            if success:
                self.publish_notification({"status": "success", "message": "Model updated successfully."})
            else:
                self.publish_notification({"status": "error", "message": "Failed to reload new model."})

        except requests.RequestException as e:
            logging.error(f"Failed to download model: {e}")
            self.publish_notification({"status": "error", "message": f"Failed to download model: {e}"})


    def handle_change_param(self, command: dict):
        """Handles updating parameters for the current agent."""
        params = command.get('params')
        if not params or not isinstance(params, dict):
            logging.error("'change_param' command missing 'params' dictionary.")
            return

        self.executor.update_agent_parameters(params)
        self.publish_notification({"status": "success", "message": "Parameters updated."})

    def publish_notification(self, message: dict):
        """Publishes a notification message to the notify topic."""
        try:
            payload = json.dumps(message)
            self.client.publish(self.notify_topic, payload)
            logging.info(f"Published notification to {self.notify_topic}: {payload}")
        except Exception as e:
            logging.error(f"Failed to publish notification: {e}")

    def run(self):
        """Connects to the MQTT broker and starts the service."""
        try:
            self.client.connect(self.broker_address, self.port, 60)
            self.client.loop_start()
            logging.info("MQTT service started.")
        except Exception as e:
            logging.error(f"An error occurred while starting MQTT service: {e}")

    def stop(self):
        """Stops the MQTT service."""
        self.client.loop_stop()
        self.client.disconnect()
        logging.info("MQTT service stopped.")
