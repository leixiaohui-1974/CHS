# chs-scada-dispatch/app.py
import logging
from api.rest_api import create_app
from data_processing.status_store import StatusStore
# Note: In a future version, we will run the MQTT consumer in a separate thread or process.
# from data_ingestion.mqtt_consumer import MqttConsumer

def main():
    """
    Main function to initialize and run the SCADA dispatch application.
    """
    # 1. Configure logging
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    # 2. Initialize the central data store
    # This object will hold the latest status of all devices.
    status_store = StatusStore()
    logging.info("StatusStore initialized.")

    # 3. Create the Flask application using the factory pattern
    # We inject the status_store dependency into the app.
    app = create_app(status_store)
    logging.info("Flask application created.")

    # (Future Step: Initialize and start the MQTT consumer in a background thread)
    # mqtt_consumer = MqttConsumer(status_store)
    # mqtt_consumer.start()
    # logging.info("MQTT Consumer started.")

    # 4. Run the Flask web server
    # host='0.0.0.0' makes it accessible from outside the container/machine.
    # debug=True is useful for development but should be False in production.
    logging.info("Starting Flask server...")
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()
