import paho.mqtt.client as mqtt
import json
import time
import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
BROKER_ADDRESS = "127.0.0.1"
PORT = 1883
CLIENT_ID = "test_publisher_mvp"

# --- Data to Simulate ---
test_payloads = [
    {
        "timestamp": None, # Will be set to current time
        "device_id": "pump_station_01",
        "values": {
            "level_sensor_1": 123.45,
            "flow_meter_2": 55.6,
            "pump1_status": 1
        }
    },
    {
        "timestamp": None, # Will be set to current time
        "device_id": "sluice_gate_03",
        "values": {
            "gate_opening": 0.75,
            "downstream_level": 12.3,
            "motor_temp": 45.2
        }
    }
]

def publish_data(client: mqtt.Client):
    """Connects and publishes a series of test data messages."""
    try:
        client.connect(BROKER_ADDRESS, PORT)
        logging.info("Test Publisher connected to MQTT Broker.")

        for data in test_payloads:
            # Update timestamp to current time in ISO 8601 format with Z
            data["timestamp"] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

            device_id = data["device_id"]
            topic = f"chs/edge/{device_id}/state"
            payload = json.dumps(data)

            result = client.publish(topic, payload)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logging.info(f"Successfully sent message to topic '{topic}': {payload}")
            else:
                logging.error(f"Failed to send message to topic {topic}, result code: {result.rc}")

            time.sleep(0.5) # Brief pause

        client.disconnect()
        logging.info("Test Publisher disconnected.")

    except ConnectionRefusedError:
        logging.error(f"Connection refused. Please ensure an MQTT broker is running at {BROKER_ADDRESS}:{PORT}.")
    except Exception as e:
        logging.error(f"An error occurred in the test publisher: {e}")

if __name__ == "__main__":
    # Use a unique client_id to avoid connection issues
    publisher_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=f"{CLIENT_ID}-{time.time()}")
    publish_data(publisher_client)
