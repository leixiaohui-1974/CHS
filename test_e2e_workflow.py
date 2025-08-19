import subprocess
import time
import requests
import paho.mqtt.client as mqtt
import json
import sys

# --- Configuration ---
SCADA_API_URL = "http://localhost:8001"
HEALTH_ENDPOINT = f"{SCADA_API_URL}/health"
STATUS_ENDPOINT = f"{SCADA_API_URL}/api/v1/system_status"
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_PREFIX = "chs/edge/status"

TEST_DEVICE_ID = "test_device_001"
TEST_PAYLOAD = {
    "level": 15.5,
    "flow_rate": 1.2,
    "timestamp": time.time()
}

def wait_for_service(url, timeout=60):
    """Polls a URL until it returns a 200 OK status or times out."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"Service at {url} is healthy.")
                return True
        except requests.ConnectionError:
            print(f"Waiting for service at {url}...")
            time.sleep(5)
    print(f"Error: Timed out waiting for service at {url}.")
    return False

def publish_mqtt_message(topic, payload):
    """Publishes a single message to the MQTT broker."""
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        client.publish(topic, json.dumps(payload))
        client.disconnect()
        print(f"Successfully published message to topic '{topic}'.")
    except Exception as e:
        print(f"Error publishing MQTT message: {e}")
        sys.exit(1)

def verify_data_in_scada(device_id, expected_level):
    """Verifies that the correct data is available via the SCADA API."""
    try:
        response = requests.get(STATUS_ENDPOINT, timeout=10)
        response.raise_for_status()
        data = response.json()

        # The API returns a list of the latest status for each device
        device_status = next((item for item in data if item.get('device_id') == device_id), None)

        if not device_status:
            print(f"Error: Device '{device_id}' not found in SCADA system status.")
            return False

        print(f"Found status for device '{device_id}': {device_status}")

        actual_level = device_status.get('level')

        assert abs(actual_level - expected_level) < 1e-9, \
            f"Assertion failed! Expected level: {expected_level}, Actual level: {actual_level}"

        print(f"SUCCESS: Data for device '{device_id}' verified in SCADA API.")
        return True

    except requests.exceptions.RequestException as e:
        print(f"Error making API call to SCADA: {e}")
        return False
    except (AssertionError, KeyError, StopIteration) as e:
        print(f"Error verifying data: {e}")
        return False

def main():
    """Main function to orchestrate the E2E test."""
    try:
        # 1. Start all services in the background
        print("Starting services with docker-compose...")
        subprocess.run(["docker-compose", "up", "-d", "--build"], check=True)

        # 2. Wait for the SCADA service to be healthy
        if not wait_for_service(HEALTH_ENDPOINT):
            raise RuntimeError("SCADA service did not become healthy.")

        # Give the MQTT service a moment to fully initialize
        time.sleep(5)

        # 3. Publish a test message from a mock edge device
        topic = f"{MQTT_TOPIC_PREFIX}/{TEST_DEVICE_ID}"
        publish_mqtt_message(topic, TEST_PAYLOAD)

        # 4. Wait for the message to be processed and verify the result
        print("Waiting for data to be processed by SCADA...")
        time.sleep(5) # Allow time for ingestion and database write

        if not verify_data_in_scada(TEST_DEVICE_ID, TEST_PAYLOAD["level"]):
            raise RuntimeError("E2E test failed: Data verification failed.")

    except (subprocess.CalledProcessError, RuntimeError) as e:
        print(f"\n--- E2E TEST FAILED: {e} ---")
        sys.exit(1)
    finally:
        # 5. Stop and remove all services
        print("\nCleaning up services with docker-compose...")
        subprocess.run(["docker-compose", "down"], check=True)
        print("Cleanup complete.")

if __name__ == "__main__":
    main()
