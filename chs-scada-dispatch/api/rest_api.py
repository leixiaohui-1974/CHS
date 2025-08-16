from flask import Flask, jsonify, request
from data_processing.timeseries_db import TimeSeriesDB
from data_ingestion.mqtt_service import MqttService
import logging

def create_rest_app(timeseries_db: TimeSeriesDB, mqtt_service: MqttService):
    """
    Creates and configures the Flask application for RESTful APIs.
    Injects dependencies to make the app modular and testable.
    """
    app = Flask(__name__)

    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    @app.route('/api/v1/system_status', methods=['GET'])
    def get_system_status():
        """
        API endpoint to get the current status of all systems from InfluxDB.
        """
        try:
            statuses = timeseries_db.get_latest_statuses()
            logging.info(f"API call to /api/v1/system_status returned status for {len(statuses)} devices.")
            return jsonify(statuses)
        except Exception as e:
            logging.error(f"Error in /api/v1/system_status: {e}", exc_info=True)
            return jsonify({"error": "An internal server error occurred"}), 500

    @app.route('/api/v1/command', methods=['POST'])
    def post_command():
        """
        API endpoint to manually issue a command to a device.
        """
        try:
            data = request.get_json()
            if not data or 'target_device_id' not in data or 'command' not in data:
                return jsonify({"error": "Invalid request body. 'target_device_id' and 'command' are required."}), 400

            device_id = data['target_device_id']
            command = data['command']

            logging.info(f"Received API request to issue command to {device_id}: {command}")
            mqtt_service.publish_command(device_id, command)

            return jsonify({"message": "Command successfully sent to the queue."}), 202
        except Exception as e:
            logging.error(f"Error in /api/v1/command: {e}", exc_info=True)
            return jsonify({"error": "An internal server error occurred"}), 500

    return app
